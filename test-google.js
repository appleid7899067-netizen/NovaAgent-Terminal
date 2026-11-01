const puppeteer = require("puppeteer-core");

(async () => {
  let browser;
  let page;

  try {
    browser = await puppeteer.connect({
      browserURL: "http://127.0.0.1:9222"
    });

    page = await browser.newPage();

    await page.goto("https://www.google.com", {
      waitUntil: "domcontentloaded",
      timeout: 60000
    });

    const result = await page.evaluate(() => ({
      title: document.title,
      url: location.href,
      body: document.body.innerText.slice(0, 500)
    }));

    console.log(JSON.stringify(result, null, 2));
  } finally {
    if (page) await page.close().catch(() => {});
    if (browser) await browser.disconnect().catch(() => {});
  }
})();
