const fs = require('fs');
const path = require('path');
const runtime = path.join(process.env.USERPROFILE || '', '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
function dependency(name) {
  try { return require(name); } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
    return require(path.join(runtime, name));
  }
}
const { chromium } = dependency('playwright');
const sharp = dependency('sharp');
const root = path.resolve(__dirname, '..');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 800, height: 800 }, deviceScaleFactor: 2 });
    async function render(name, width) {
      await page.setViewportSize({ width, height: 800 });
      await page.setContent(`<html><head><style>html,body{margin:0;padding:0;background:transparent}svg{display:block}</style></head><body>${fs.readFileSync(path.join(root, name), 'utf8')}</body></html>`);
      return page.screenshot({ omitBackground: true });
    }
    if (process.argv.includes('--logo')) {
      await sharp(await render('logo.svg', 800)).resize(800, 800).png().toFile(path.join(root, 'logo.png'));
      const high = await browser.newPage({ viewport: { width: 800, height: 800 }, deviceScaleFactor: 4 });
      await high.setContent(`<html><head><style>html,body{margin:0;padding:0;background:transparent}svg{display:block}</style></head><body>${fs.readFileSync(path.join(root, 'logo.svg'), 'utf8')}</body></html>`);
      await high.screenshot({ omitBackground: true, path: path.join(root, 'logo-3200.png') });
      console.log('Rendered pure logo PNGs.');
    } else if (process.argv.includes('--white')) {
      const name = process.argv.includes('--zh') ? 'logo-zh-white3d' : 'logo-en-white3d';
      const width = process.argv.includes('--zh') ? 3074 : 4262;
      const buffer = await render(name + '.svg', width);
      await sharp(buffer).resize(width, 800).png().toFile(path.join(root, name + '.png'));
      await sharp(buffer).png().toFile(path.join(root, name + '@2x.png'));
      console.log('Rendered white logo wordmark: transparent PNG and double resolution PNG.');
    } else {
      const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'manifest.json'), 'utf8'));
      for (const item of manifest) {
        const name = item.svg.slice(0, -4);
        const buffer = await render(item.svg, item.width);
        await sharp(buffer).resize(item.width, 800).png().toFile(path.join(root, name + '.png'));
        await sharp(buffer).png().toFile(path.join(root, name + '@2x.png'));
      }
      console.log('Rendered 12 wordmark PNGs.');
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
