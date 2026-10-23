const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const { pathToFileURL, fileURLToPath } = require('url');
let playwright;
try { playwright = require('playwright'); } catch (error) {
  if (error.code !== 'MODULE_NOT_FOUND') throw error;
  playwright = require(path.join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
}
const root = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '..');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true, args: ['--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    const requests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push(request.url()));
    const preview = path.join(root, 'src/输出/预览.html');
    await page.goto(pathToFileURL(preview).href);
    assert.equal(await page.locator('article img').count(), 6);
    assert.ok(await page.locator('article img').evaluateAll(images => images.every(im => im.complete && im.naturalWidth > 0)));
    for (const url of await page.locator('a').evaluateAll(links => links.map(a => a.href))) {
      assert.ok(fs.existsSync(fileURLToPath(url)), url);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const manifest = JSON.parse(fs.readFileSync(path.join(root, 'src/manifest.json'), 'utf8'));
    for (const item of manifest) {
      await page.goto(pathToFileURL(path.join(root, item.svg)).href);
      assert.equal(await page.locator('svg').count(), 2);
      assert.ok(await page.locator('#pixel-wordmark rect').count() > 0);
    }
    await page.goto(pathToFileURL(path.join(root, 'logo.html')).href);
    await page.waitForFunction(() => window.cubeCluster && document.querySelector('canvas').width > 0);
    await page.locator('#scene').focus();
    await page.keyboard.press('ArrowRight');
    assert.ok(await page.evaluate(() => Math.abs(cubeCluster.view.azimuth - cubeCluster.defaultView.azimuth) > .001));
    await page.locator('#reset').click();
    await page.waitForTimeout(600);
    assert.ok(await page.evaluate(() => Object.keys(cubeCluster.defaultView).every(key => Math.abs(cubeCluster.view[key] - cubeCluster.defaultView[key]) < .001)));
    assert.equal(errors.length, 0, errors.join('\n'));
    for (const request of requests) {
      assert.ok(request.startsWith('file:'), request);
      const relative = path.relative(root, fileURLToPath(request));
      assert.ok(!relative.startsWith('..') && !path.isAbsolute(relative) && !relative.split(path.sep).includes('备份'), request);
    }
    console.log(JSON.stringify({ offline_preview: true, six_svg_files_loaded: true, download_links: true, narrow_screen: true,
      rotation_and_reset: true, no_requests_outside_package: true, no_backup_dependency: true, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
