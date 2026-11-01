const { chromium } = require("playwright-core");

(async () => {
  let browser;
  let page;

  try {
    browser = await chromium.connectOverCDP(
      "http://127.0.0.1:9222",
      { timeout: 30000 }
    );

    const context = browser.contexts()[0];

    if (!context) {
      throw new Error("ไม่พบ Browser Context");
    }

    page = await context.newPage();

    await page.goto("https://example.com", {
      waitUntil: "domcontentloaded",
      timeout: 60000
    });

    console.log("Title:", await page.title());
    console.log("URL:", page.url());

    const heading = await page
      .locator("h1")
      .first()
      .textContent()
      .catch(() => "");

    console.log("Heading:", heading?.trim() || "ไม่พบ h1");
  } finally {
    if (page) {
      await page.close().catch(() => {});
    }
  }
})();
