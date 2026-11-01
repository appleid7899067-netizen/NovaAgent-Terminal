#!/usr/bin/env node
/**
 * browser_driver.mjs — Node Playwright sidecar for the Python browser_service.
 *
 * WHY THIS EXISTS
 * ---------------
 * The Termux/Android Python environment has no `playwright` pip package and
 * cannot install one (no wheels for the platform). But the *Node* `playwright`
 * package is installed globally and can drive the system `chromium-browser`
 * over CDP (verified). This driver bridges the two: Python speaks line-delimited
 * JSON-RPC on stdin/stdout, this process executes the equivalent Playwright
 * call and writes a JSON result line back.
 *
 * PROTOCOL
 * --------
 * Request  (one JSON object per line on stdin):
 *   {"id": 1, "op": "launch", "args": {...}}
 * Response (one JSON object per line on stdout):
 *   {"id": 1, "ok": true, "result": {...}}
 *   {"id": 1, "ok": false, "error": "message"}
 *
 * stdout is RESERVED for protocol frames. All logging goes to stderr.
 *
 * OPS (implemented incrementally; unknown ops return an error so the Python
 * side can fall back cleanly):
 *   ping                                   -> {pong:true, version}
 *   launch        {headless,args,cdpEndpoint}  -> {via:"cdp"|"launch"}
 *   page_goto     {url,timeout}            -> {title,url,status}
 *   page_title    {}                       -> {title}
 *   page_url      {}                       -> {url}
 *   page_snapshot {}                       -> {html}   (raw HTML of body)
 *   page_evaluate {script,arg}             -> {result}
 *   page_screenshot {fullPage,path}        -> {path}
 *   page_click    {selector,timeout}       -> {ok}
 *   page_fill     {selector,text,timeout}  -> {ok}
 *   page_select   {selector,value,timeout} -> {ok}
 *   page_scroll   {dx,dy}                  -> {scrollX,scrollY}
 *   page_wait_for {selector,timeout,state} -> {ok}
 *   page_wait_timeout {ms}                 -> {ok}
 *   page_text     {selector,timeout}       -> {text}
 *   page_press    {key}                    -> {ok}
 *   page_back     {timeout}                -> {title,url}
 *   page_forward  {timeout}                -> {title,url}
 *   page_url      {}                       -> {url}
 *   close         {}                       -> {ok}
 */

import { chromium } from 'playwright';
import { spawn } from 'child_process';
import net from 'net';
import readline from 'readline';
import path from 'path';
import fs from 'fs';
import os from 'os';

const DRIVER_VERSION = '1.0.1';

// ---------------------------------------------------------------------------
// Writable temp dir resolution.
// Termux/Android has NO /tmp. Chromium aborts at startup with
// "Cannot read and write to its data directory" if the profile path is not
// writable, and with stdio ignored the death is silent -> CDP never answers.
// Prefer TMPDIR (Termux sets it to $PREFIX/tmp), then os.tmpdir(), then
// $PREFIX/tmp, then the current dir. Return the first that is writable.
// ---------------------------------------------------------------------------
function pickWritableTmpDir() {
  const candidates = [
    process.env.TMPDIR,
    process.env.PREFIX ? path.join(process.env.PREFIX, 'tmp') : null,
    os.tmpdir(),
    process.cwd(),
  ].filter(Boolean);
  for (const dir of candidates) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      fs.accessSync(dir, fs.constants.W_OK);
      return dir;
    } catch (_) { /* try next */ }
  }
  return process.cwd();
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let browser = null;      // Playwright Browser (CDP or launched)
let context = null;      // BrowserContext
let page = null;         // Page
let childProc = null;    // spawned chromium process when we own it
let via = null;          // "cdp" | "launch"
let profileDir = null;

const log = (...a) => process.stderr.write('[driver] ' + a.join(' ') + '\n');

// ---------------------------------------------------------------------------
// JSHandle registry: element ops pass a numeric id instead of a live handle.
// ---------------------------------------------------------------------------
let handleSeq = 0;
const handleMap = new Map(); // id -> JSHandle

function storeHandle(handle, isElement) {
  const id = ++handleSeq;
  handleMap.set(id, handle);
  return id;
}
function getHandle(id) {
  const h = handleMap.get(id);
  if (!h) throw new Error(`stale handle id ${id}`);
  return h;
}
function dropHandle(id) {
  const h = handleMap.get(id);
  if (h) { try { h.dispose(); } catch (_) {} handleMap.delete(id); }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const p = srv.address().port;
      srv.close(() => resolve(p));
    });
  });
}

function waitForCdp(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  const url = `http://127.0.0.1:${port}/json/version`;
  return new Promise((resolve) => {
    const tick = async () => {
      try {
        const res = await fetch(url);
        if (res.ok) return resolve(true);
      } catch (_) { /* not up yet */ }
      if (Date.now() > deadline) return resolve(false);
      setTimeout(tick, 250);
    };
    tick();
  });
}

// ---------------------------------------------------------------------------
// Ops
// ---------------------------------------------------------------------------
const ops = {
  async ping() {
    return { pong: true, version: DRIVER_VERSION, via };
  },

  async launch(a) {
    const headless = a.headless !== false;
    const args = Array.isArray(a.args) ? a.args.slice() : [];
    // Termux/Android: /tmp does not exist. Chromium fails with
    // "Cannot read and write to its data directory" and dies silently.
    // Use a real writable temp dir instead.
    const tmpRoot = pickWritableTmpDir();
    profileDir = a.userDataDir || path.join(tmpRoot, `cow-browser-profile-${process.pid}`);

    // Preferred path on Termux: we own the browser process and attach over CDP.
    if (a.cdpEndpoint) {
      browser = await chromium.connectOverCDP(a.cdpEndpoint);
      via = 'cdp';
    } else {
      const exe = a.executable || 'chromium-browser';
      const port = await freePort();
      const spawnArgs = [
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${profileDir}`,
        headless ? '--headless=new' : '--start-maximized',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        ...args,
        'about:blank',
      ];
      log('spawning', exe, 'port', port);
      // Capture chromium output to OUR stderr (stdout is reserved for the
      // JSON-RPC protocol). With stdio:'ignore' a startup failure (bad
      // profile dir, sandbox, OOM) is invisible and CDP just times out.
      childProc = spawn(exe, spawnArgs, {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
      });
      childProc.stdout.on('data', (d) => process.stderr.write('[chromium:out] ' + d));
      childProc.stderr.on('data', (d) => process.stderr.write('[chromium:err] ' + d));
      childProc.on('exit', (code) => log('chromium exited code', code));

      const up = await waitForCdp(port, 15000);
      if (!up) throw new Error(`chromium did not expose CDP on port ${port}`);
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
      via = 'cdp';
    }

    // Reuse the default context/page the browser already has.
    const ctxs = browser.contexts();
    context = ctxs.length ? ctxs[0] : await browser.newContext();
    const pages = context.pages();
    page = pages.length ? pages[0] : await context.newPage();
    return { via, profileDir };
  },

  async page_goto(a) {
    if (!page) throw new Error('no page');
    const resp = await page.goto(a.url, {
      wait_until: a.waitUntil || 'domcontentloaded',
      timeout: a.timeout || 30000,
    });
    return { title: await page.title(), url: page.url(), status: resp ? resp.status() : null };
  },

  async page_title() { if (!page) throw new Error('no page'); return { title: await page.title() }; },
  async page_url() { if (!page) throw new Error('no page'); return { url: page.url() }; },

  async page_snapshot() {
    if (!page) throw new Error('no page');
    const html = await page.evaluate('document.body ? document.body.innerHTML : ""');
    return { html };
  },

  async page_evaluate(a) {
    if (!page) throw new Error('no page');
    const result = a.arg !== undefined
      ? await page.evaluate(a.script, a.arg)
      : await page.evaluate(a.script);
    return { result };
  },

  // Evaluate an expression and return a *handle* we can act on later.
  // The Python side keeps only the numeric handle id; element ops below accept
  // that id so we never have to round-trip a DOM node through JSON.
  async page_evaluate_handle(a) {
    if (!page) throw new Error('no page');
    const handle = a.arg !== undefined
      ? await page.evaluateHandle(a.script, a.arg)
      : await page.evaluateHandle(a.script);
    const isElement = await handle.evaluate((el) => !!(el && el.nodeType === 1)).catch(() => false);
    const id = storeHandle(handle, isElement);
    return { handleId: id, isElement };
  },

  async page_wait_for_load_state(a) {
    if (!page) throw new Error('no page');
    await page.waitForLoadState(a.state || 'load', { timeout: a.timeout || 30000 });
    return { ok: true };
  },

  // ---- element ops (operate on a handle id from page_evaluate_handle) ----
  async element_click(a) {
    const el = getHandle(a.handleId);
    await el.click({ timeout: a.timeout || 30000 });
    return { ok: true };
  },

  async element_fill(a) {
    const el = getHandle(a.handleId);
    await el.fill(a.text, { timeout: a.timeout || 30000 });
    return { ok: true };
  },

  async element_select(a) {
    const el = getHandle(a.handleId);
    await el.selectOption(a.value, { timeout: a.timeout || 30000 });
    const selected = await el.evaluate((e) => e.value);
    return { selected };
  },

  async element_evaluate(a) {
    const el = getHandle(a.handleId);
    const result = await el.evaluate(a.script);
    return { result };
  },

  async element_tag(a) {
    const el = getHandle(a.handleId);
    const tag = await el.evaluate((e) => (e.tagName || '').toLowerCase());
    return { tag };
  },

  async element_dispose(a) {
    dropHandle(a.handleId);
    return { ok: true };
  },

  async page_screenshot(a) {
    if (!page) throw new Error('no page');
    await page.screenshot({ path: a.path, full_page: !!a.fullPage });
    return { path: a.path };
  },

  async page_click(a) {
    if (!page) throw new Error('no page');
    await page.click(a.selector, { timeout: a.timeout || 30000 });
    return { ok: true };
  },

  async page_fill(a) {
    if (!page) throw new Error('no page');
    await page.fill(a.selector, a.text, { timeout: a.timeout || 30000 });
    return { ok: true };
  },

  async page_select(a) {
    if (!page) throw new Error('no page');
    await page.selectOption(a.selector, a.value, { timeout: a.timeout || 30000 });
    return { ok: true };
  },

  async page_scroll(a) {
    if (!page) throw new Error('no page');
    await page.mouse.wheel(a.dx || 0, a.dy || 0);
    await page.waitForTimeout(300);
    const pos = await page.evaluate('({x: window.scrollX, y: window.scrollY})');
    return pos;
  },

  async page_wait_for(a) {
    if (!page) throw new Error('no page');
    await page.waitForSelector(a.selector, {
      timeout: a.timeout || 30000,
      state: a.state || 'visible',
    });
    return { ok: true };
  },

  async page_wait_timeout(a) {
    if (!page) throw new Error('no page');
    await page.waitForTimeout(a.ms || 0);
    return { ok: true };
  },

  async page_text(a) {
    if (!page) throw new Error('no page');
    const text = await page.textContent(a.selector, { timeout: a.timeout || 5000 });
    return { text };
  },

  async page_press(a) {
    if (!page) throw new Error('no page');
    await page.keyboard.press(a.key);
    await page.waitForTimeout(300);
    return { ok: true };
  },

  async page_back(a) {
    if (!page) throw new Error('no page');
    await page.goBack({ wait_until: 'domcontentloaded', timeout: a.timeout || 10000 });
    return { title: await page.title(), url: page.url() };
  },

  async page_forward(a) {
    if (!page) throw new Error('no page');
    await page.goForward({ wait_until: 'domcontentloaded', timeout: a.timeout || 10000 });
    return { title: await page.title(), url: page.url() };
  },

  async close() {
    try { if (browser) await browser.close(); } catch (e) { log('browser close:', e.message); }
    try { if (childProc && !childProc.killed) childProc.kill('SIGKILL'); } catch (_) {}
    browser = null; context = null; page = null; childProc = null; via = null;
    return { ok: true };
  },
};

// ---------------------------------------------------------------------------
// Main loop: read line-delimited JSON, dispatch, write JSON response
// ---------------------------------------------------------------------------
const rl = readline.createInterface({ input: process.stdin });

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

// Ops must run strictly in order: 'line' fires on every input line without
// waiting for the previous async handler, so a slow launch() would still be
// running when page_goto() arrives -> "no page". Chain every request onto a
// single promise queue so each op completes before the next starts.
let queue = Promise.resolve();

function handleLine(line) {
  line = line.trim();
  if (!line) return;
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (e) {
    send({ id: null, ok: false, error: 'bad json: ' + e.message });
    return;
  }
  const { id, op, args } = msg;
  const fn = ops[op];
  if (!fn) {
    send({ id, ok: false, error: `unknown op: ${op}` });
    return;
  }
  queue = queue.then(async () => {
    try {
      const result = await fn(args || {});
      send({ id, ok: true, result });
    } catch (e) {
      send({ id, ok: false, error: e.message || String(e) });
    }
  });
}

rl.on('line', handleLine);

rl.on('close', async () => {
  try { await ops.close(); } catch (_) {}
  process.exit(0);
});

process.on('SIGTERM', async () => { try { await ops.close(); } catch (_) {} process.exit(0); });
process.on('SIGINT', async () => { try { await ops.close(); } catch (_) {} process.exit(0); });

log('driver ready, version', DRIVER_VERSION);
