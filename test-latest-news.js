const puppeteer = require("puppeteer-core");
const fs = require("fs/promises");

const CDP_URL = "http://127.0.0.1:9222";
const NAVIGATION_TIMEOUT = 60000;
const TARGETS = [
  {
    name: "Yandex news search",
    url: "https://yandex.com/search/?text=latest%20world%20news",
    selector: "body"
  },
  {
    name: "BBC World",
    url: "https://www.bbc.com/news/world",
    selector: "body"
  },
  {
    name: "Al Jazeera News",
    url: "https://www.aljazeera.com/news/",
    selector: "body"
  }
];

function cleanText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function detectBlockedPage(title, text, finalUrl) {
  const haystack = `${title} ${text} ${finalUrl}`.toLowerCase();
  const markers = [
    "captcha",
    "unusual traffic",
    "access denied",
    "robot check",
    "are you a robot",
    "требуется подтверждение"
  ];
  return markers.some((marker) => haystack.includes(marker));
}

async function scrapeOneTab(browser, target, index) {
  const page = await browser.newPage();
  try {
    console.log(`[Tab ${index}] เปิด ${target.url}`);
    await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 });
    page.setDefaultNavigationTimeout(NAVIGATION_TIMEOUT);
    page.setDefaultTimeout(15000);
    await page.goto(target.url, { waitUntil: "domcontentloaded", timeout: NAVIGATION_TIMEOUT });
    await new Promise((resolve) => setTimeout(resolve, 1500));
    const result = await page.evaluate((selector) => {
      const selected = document.querySelector(selector);
      return {
        title: document.title,
        url: location.href,
        text: selected?.innerText || document.body?.innerText || "",
        links: [...document.querySelectorAll("a")].slice(0, 30).map((link) => ({
          text: link.innerText.trim(),
          href: link.href
        }))
      };
    }, target.selector);
    const title = cleanText(result.title);
    const text = cleanText(result.text).slice(0, 4000);
    const blocked = detectBlockedPage(title, text, result.url);
    const cleaned = {
      name: target.name,
      requestedUrl: target.url,
      finalUrl: result.url,
      title,
      text,
      links: result.links,
      success: !blocked,
      blocked
    };
    console.log(`[Tab ${index}] ${blocked ? "ถูกบล็อก/ต้องยืนยันตัวตน" : "สำเร็จ"}: ${cleaned.title}`);
    return cleaned;
  } catch (error) {
    console.error(`[Tab ${index}] ล้มเหลว: ${error.message}`);
    return { name: target.name, requestedUrl: target.url, success: false, error: error.message };
  } finally {
    await page.close().catch(() => {});
  }
}

async function main() {
  let browser;
  try {
    browser = await puppeteer.connect({ browserURL: CDP_URL, defaultViewport: null });
    console.log("เชื่อมต่อ Chromium ผ่าน CDP สำเร็จ");
    const existingPages = await browser.pages();
    console.log(`มี Tab เดิมอยู่ ${existingPages.length} Tab`);
    const results = await Promise.all(TARGETS.map((target, index) => scrapeOneTab(browser, target, index + 1)));
    const output = { scrapedAt: new Date().toISOString(), query: "latest world news", searchProvider: "Yandex", count: results.length, results };
    await fs.writeFile("latest-news-result.json", JSON.stringify(output, null, 2), "utf8");
    console.log(`เสร็จแล้ว ${results.length} Tab; บันทึก latest-news-result.json`);
    console.log(results.map(({ name, title, success }) => ({ name, title, success })));
  } catch (error) {
    console.error("เชื่อมต่อหรือประมวลผลล้มเหลว:", error.message);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.disconnect().catch(() => {});
  }
}

main();
