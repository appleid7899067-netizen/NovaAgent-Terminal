#!/usr/bin/env node
'use strict';

const readline = require('node:readline');
const fs = require('node:fs/promises');
const path = require('node:path');
const puppeteer = require('puppeteer-core');

const ROOT = path.resolve(process.env.NOVA_ROOT || '.nova-workspace');
const CDP_URL = process.env.CDP_URL || 'http://127.0.0.1:9222';
const CAPTURES = path.join(ROOT, 'captures');

let cwd = ROOT;
let browser = null;
const namedTabs = new Map();

function prompt() {
  return `nova:${path.relative(ROOT, cwd) || '/'}$ `;
}

function splitArgs(line) {
  return line.match(/(?:[^\s"]+|"[^"]*")+/g)?.map((x) =>
    x.startsWith('"') && x.endsWith('"') ? x.slice(1, -1) : x
  ) || [];
}

function safePath(input = '.') {
  const target = path.resolve(cwd, input);
  if (target !== ROOT && !target.startsWith(`${ROOT}${path.sep}`)) {
    throw new Error('ไม่อนุญาตให้ออกจาก Nova workspace');
  }
  return target;
}

function stamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

async function getBrowser() {
  if (browser) return browser;
  try {
    browser = await puppeteer.connect({
      browserURL: CDP_URL,
      defaultViewport: null,
    });
    return browser;
  } catch (error) {
    throw new Error(`เชื่อม Chromium/CDP ไม่ได้: ${error.message}`);
  }
}

async function cmdHelp() {
  console.log(`
Nova Computer commands

File workspace:
  pwd                         แสดงโฟลเดอร์ปัจจุบัน
  ls [path]                   แสดงไฟล์
  cd <path>                   เปลี่ยนโฟลเดอร์
  mkdir <path>                สร้างโฟลเดอร์
  write <file> <text>         เขียนไฟล์ข้อความ
  cat <file>                  อ่านไฟล์
  rm <file>                   ลบไฟล์ใน workspace

Browser / scraping:
  browser                     ตรวจสอบการเชื่อมต่อ CDP
  open <url> [name]           เปิด Tab และเก็บชื่อ Tab
  tabs                        แสดง Tab ที่เปิดอยู่
  close <name>                ปิด Tab ที่สคริปต์เปิด
  scrape <url> <selector>     ดึงข้อมูลรายการเป็น JSON
  capture <url> [name]        เก็บ screenshot + HTML + metadata

General:
  clear                       ล้างหน้าจอ
  help                        แสดงความช่วยเหลือ
  exit                        ออกจาก Nova Computer

ตัวอย่าง:
  browser
  open https://example.com demo
  scrape https://example.com body
  capture https://example.com example
`);
}

async function cmdLs(input = '.') {
  const dir = safePath(input);
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    console.log(`${entry.isDirectory() ? '[DIR] ' : '      '}${entry.name}`);
  }
}

async function cmdScrape(url, selector = 'body') {
  if (!url) throw new Error('ใช้: scrape <url> <selector>');
  const b = await getBrowser();
  const page = await b.newPage();
  try {
    await page.setDefaultNavigationTimeout(60000);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const items = await page.$$eval(selector, (elements) => elements.map((el) => {
      const clean = (value) => String(value || '').replace(/\s+/g, ' ').trim();
      const heading = el.querySelector('h1,h2,h3,h4,h5,h6,.title');
      const link = el.querySelector('a');
      const image = el.querySelector('img');
      return {
        title: clean(heading?.textContent),
        text: clean(el.textContent),
        url: link?.href || '',
        image: image?.src || '',
      };
    }));
    const result = {
      scrapedAt: new Date().toISOString(),
      requestedUrl: url,
      finalUrl: page.url(),
      title: await page.title(),
      selector,
      count: items.length,
      items,
    };
    await fs.mkdir(ROOT, { recursive: true });
    const output = path.join(ROOT, `scrape-${stamp()}.json`);
    await fs.writeFile(output, JSON.stringify(result, null, 2));
    console.log(JSON.stringify({ output, count: items.length, title: result.title }, null, 2));
  } finally {
    await page.close().catch(() => {});
  }
}

async function cmdCapture(url, name = 'page') {
  if (!url) throw new Error('ใช้: capture <url> [name]');
  const b = await getBrowser();
  const page = await b.newPage();
  const dir = path.join(CAPTURES, `${stamp()}-${String(name).replace(/[^a-zA-Z0-9_-]/g, '-')}`);
  await fs.mkdir(dir, { recursive: true });
  try {
    await page.setDefaultNavigationTimeout(60000);
    await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 });
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await new Promise((resolve) => setTimeout(resolve, 1200));
    const html = await page.content();
    const metadata = {
      capturedAt: new Date().toISOString(),
      requestedUrl: url,
      finalUrl: page.url(),
      title: await page.title(),
    };
    await fs.writeFile(path.join(dir, 'page.html'), html);
    await page.screenshot({ path: path.join(dir, 'screenshot.png'), fullPage: true });
    await fs.writeFile(path.join(dir, 'metadata.json'), JSON.stringify(metadata, null, 2));
    console.log(JSON.stringify({ directory: dir, ...metadata }, null, 2));
  } finally {
    await page.close().catch(() => {});
  }
}

async function cmdBrowser() {
  const b = await getBrowser();
  const pages = await b.pages();
  console.log(`เชื่อมต่อสำเร็จ: ${pages.length} Tab`);
  console.log(`CDP: ${CDP_URL}`);
}

async function cmdOpen(url, name = `tab-${namedTabs.size + 1}`) {
  if (!url) throw new Error('ใช้: open <url> [name]');
  const b = await getBrowser();
  const page = await b.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  namedTabs.set(name, page);
  console.log(`เปิด ${name}: ${page.url()}`);
}

async function cmdTabs() {
  const b = await getBrowser();
  const pages = await b.pages();
  for (const [index, page] of pages.entries()) {
    const name = [...namedTabs.entries()].find(([, value]) => value === page)?.[0] || '-';
    console.log(`${index + 1}. ${name} ${await page.title().catch(() => '')} ${page.url()}`);
  }
}

async function cmdClose(name) {
  const page = namedTabs.get(name);
  if (!page) throw new Error(`ไม่พบ Tab: ${name}`);
  await page.close();
  namedTabs.delete(name);
  console.log(`ปิด ${name}`);
}

async function runCommand(line) {
  const args = splitArgs(line);
  const command = args.shift()?.toLowerCase();
  if (!command) return true;
  switch (command) {
    case 'help': await cmdHelp(); break;
    case 'pwd': console.log(cwd); break;
    case 'ls': await cmdLs(args[0]); break;
    case 'cd': cwd = safePath(args[0] || ROOT); break;
    case 'mkdir': if (!args[0]) throw new Error('ใช้: mkdir <path>'); await fs.mkdir(safePath(args[0]), { recursive: true }); break;
    case 'write': {
      if (!args[0]) throw new Error('ใช้: write <file> <text>');
      await fs.mkdir(path.dirname(safePath(args[0])), { recursive: true });
      await fs.writeFile(safePath(args[0]), args.slice(1).join(' '), 'utf8');
      console.log(`เขียนไฟล์ ${safePath(args[0])}`);
      break;
    }
    case 'cat': if (!args[0]) throw new Error('ใช้: cat <file>'); console.log(await fs.readFile(safePath(args[0]), 'utf8')); break;
    case 'rm': if (!args[0]) throw new Error('ใช้: rm <file>'); await fs.rm(safePath(args[0]), { recursive: true, force: true }); break;
    case 'browser': await cmdBrowser(); break;
    case 'open': await cmdOpen(args[0], args[1]); break;
    case 'tabs': await cmdTabs(); break;
    case 'close': if (!args[0]) throw new Error('ใช้: close <name>'); await cmdClose(args[0]); break;
    case 'scrape': await cmdScrape(args[0], args[1] || 'body'); break;
    case 'capture': await cmdCapture(args[0], args[1] || 'page'); break;
    case 'clear': console.clear(); break;
    case 'exit': case 'quit': return false;
    default: console.log(`ไม่รู้จักคำสั่ง: ${command} — พิมพ์ help`);
  }
  return true;
}

async function main() {
  await fs.mkdir(ROOT, { recursive: true });
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, prompt: prompt() });
  console.log('Nova Computer พร้อมใช้งาน — พิมพ์ help เพื่อดูคำสั่ง');
  rl.prompt();
  for await (const line of rl) {
    try {
      const keepGoing = await runCommand(line.trim());
      if (!keepGoing) break;
    } catch (error) {
      console.error(`Error: ${error.message}`);
    }
    rl.setPrompt(prompt());
    rl.prompt();
  }
  for (const page of namedTabs.values()) await page.close().catch(() => {});
  if (browser) await browser.disconnect().catch(() => {});
  rl.close();
  console.log('ปิด Nova Computer แล้ว');
}

main().catch((error) => { console.error(error); process.exit(1); });
