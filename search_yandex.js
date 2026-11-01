const puppeteer = require('puppeteer-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
puppeteer.use(stealth);

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto('https://yandex.com', {waitUntil: 'networkidle2'});
  await page.type('input[name="text"]', 'AI Agent Tools 2026', {delay: 100});
  await page.keyboard.press('Enter');
  await page.waitForNavigation();
  console.log("⚔️ บอสครับ! ผมทะลวงเข้า Yandex สำเร็จแล้ว!");
  await browser.close();
})();
