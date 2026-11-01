const puppeteer = require("puppeteer-core");

(async () => {
  let browser;
  let page;

  try {
    browser = await puppeteer.connect({
      browserURL: "http://127.0.0.1:9222",
      defaultViewport: {
        width: 1280,
        height: 900
      }
    });

    page = await browser.newPage();

    await page.goto("https://example.com", {
      waitUntil: "networkidle2",
      timeout: 60000
    });

    await new Promise(resolve => setTimeout(resolve, 1000));

    const result = await page.evaluate(() => ({
      title: document.title,
      url: location.href,
      h1: document.querySelector("h1")?.textContent?.trim() || "",
      body: document.body?.innerText?.trim().slice(0, 500) || ""
    }));

    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error("เกิดข้อผิดพลาด:", error.message);
    process.exitCode = 1;
  } finally {
    if (page) await page.close().catch(() => {});
    if (browser) await browser.disconnect().catch(() => {});
  }
})();
