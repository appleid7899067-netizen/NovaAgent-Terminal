const puppeteer = require("puppeteer-core");
const fs = require("fs/promises");

const CDP_URL = "http://127.0.0.1:9222";

const TARGETS = [
  {
    name: "Example",
    url: "https://example.com",
    selector: "body"
  },
  {
    name: "Google",
    url: "https://www.google.com",
    selector: "body"
  },
  {
    name: "Puter",
    url: "https://puter.com",
    selector: "body"
  }
];

const NAVIGATION_TIMEOUT = 60000;

function cleanText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

async function scrapeOneTab(browser, target, index) {
  const page = await browser.newPage();

  try {
    console.log(`[Tab ${index}] เปิด ${target.url}`);

    await page.setViewport({
      width: 1280,
      height: 900,
      deviceScaleFactor: 1
    });

    page.setDefaultNavigationTimeout(NAVIGATION_TIMEOUT);
    page.setDefaultTimeout(15000);

    await page.goto(target.url, {
      waitUntil: "domcontentloaded",
      timeout: NAVIGATION_TIMEOUT
    });

    // รอให้ JavaScript ฝั่งเว็บไซต์ทำงานเล็กน้อย
    await new Promise(resolve => setTimeout(resolve, 1000));

    const result = await page.evaluate((selector) => {
      const selected = document.querySelector(selector);

      return {
        title: document.title,
        url: location.href,
        text: selected?.innerText || document.body?.innerText || "",
        links: [...document.querySelectorAll("a")]
          .slice(0, 20)
          .map((link) => ({
            text: link.innerText.trim(),
            href: link.href
          }))
      };
    }, target.selector);

    const cleaned = {
      name: target.name,
      requestedUrl: target.url,
      finalUrl: result.url,
      title: cleanText(result.title),
      text: cleanText(result.text).slice(0, 2000),
      links: result.links,
      success: true
    };

    console.log(`[Tab ${index}] สำเร็จ: ${cleaned.title}`);

    return cleaned;
  } catch (error) {
    console.error(`[Tab ${index}] ล้มเหลว: ${error.message}`);

    return {
      name: target.name,
      requestedUrl: target.url,
      success: false,
      error: error.message
    };
  } finally {
    // ปิดเฉพาะ Tab นี้ ไม่ปิด Chromium หลัก
    await page.close().catch(() => {});
  }
}

async function main() {
  let browser;

  try {
    browser = await puppeteer.connect({
      browserURL: CDP_URL,
      defaultViewport: null
    });

    console.log("เชื่อมต่อ Chromium ผ่าน CDP สำเร็จ");

    const existingPages = await browser.pages();
    console.log(`มี Tab เดิมอยู่ ${existingPages.length} Tab`);

    // เปิดและประมวลผลหลาย Tab พร้อมกัน
    const results = await Promise.all(
      TARGETS.map((target, index) =>
        scrapeOneTab(browser, target, index + 1)
      )
    );

    await fs.writeFile(
      "multi-tabs-result.json",
      JSON.stringify(
        {
          scrapedAt: new Date().toISOString(),
          count: results.length,
          results
        },
        null,
        2
      ),
      "utf8"
    );

    console.log("");
    console.log(`เสร็จแล้วทั้งหมด ${results.length} Tab`);
    console.log("บันทึกผลลัพธ์ที่ multi-tabs-result.json");

    console.log(
      results.map((result) => ({
        name: result.name,
        title: result.title,
        success: result.success
      }))
    );
  } catch (error) {
    console.error("เชื่อมต่อหรือประมวลผลล้มเหลว:", error.message);
    process.exitCode = 1;
  } finally {
    if (browser) {
      // ตัดการเชื่อมต่อ แต่ไม่ปิด Chromium ที่เปิดอยู่
      await browser.disconnect().catch(() => {});
    }
  }
}

main();
