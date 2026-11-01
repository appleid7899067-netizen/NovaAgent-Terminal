const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.connect({
    browserURL: "http://127.0.0.1:9222"
  });

  const page = await browser.newPage();

  await page.goto("https://example.com", {
    waitUntil: "domcontentloaded",
    timeout: 60000
  });

  const result = await page.evaluate(() => ({
    title: document.title,
    headings: [...document.querySelectorAll("h1, h2, h3, h4, h5, h6")]
      .map(el => ({
        tag: el.tagName,
        text: el.textContent.trim()
      })),
    bodyText: document.body.innerText.trim(),
    htmlStart: document.documentElement.outerHTML.slice(0, 1000)
  }));

  console.log(JSON.stringify(result, null, 2));

  await page.close();
  await browser.disconnect();
})();
