const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

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
const output = path.join(root, 'docs', 'images');

// 从定稿成品与原始三维场景生成文档配图。
async function build() {
  fs.mkdirSync(output, { recursive: true });
  const variants = [
    ['logo', '#f3f6fa'],
    ...['zh', 'en'].flatMap(language => [
      [`logo-${language}-blue`, '#f3f6fa'],
      [`logo-${language}-black`, '#ffffff'],
      [`logo-${language}-white`, '#182332'],
      [`logo-${language}-white3d`, '#182332'],
    ]),
  ];
  for (const [name, background] of variants) {
    const isSymbol = name === 'logo';
    const width = isSymbol ? 640 : 1400;
    const height = isSymbol ? 640 : 360;
    const image = await sharp(path.join(root, `${name}.png`))
      .resize(width - 96, height - 80, { fit: 'inside' }).png().toBuffer();
    await sharp({ create: { width, height, channels: 4, background } })
      .composite([{ input: image, gravity: 'centre' }])
      .png().toFile(path.join(output, `${name}.png`));
  }

  const browser = await chromium.launch({ headless: true, args: ['--enable-unsafe-swiftshader'] });
  try {
    const scene = await browser.newPage();
    await scene.goto(pathToFileURL(path.join(root, 'logo.html')).href);
    await scene.waitForFunction(() => Boolean(window.cubeCluster));
    const defaults = await scene.evaluate(() => window.cubeCluster.defaultView);
    const views = [
      ['view-front', defaults],
      ['view-oblique', { ...defaults, azimuth: Math.PI / 3, elevation: Math.PI / 9 }],
      ['view-side', { ...defaults, azimuth: defaults.azimuth - Math.PI / 4, elevation: 0, halfExtent: 1.5 }],
      ['view-top', { ...defaults, azimuth: Math.PI / 4, elevation: Math.PI / 2 - 0.00001 }],
    ];
    const render = await browser.newPage({ viewport: { width: 960, height: 960 }, deviceScaleFactor: 1 });
    for (const [name, view] of views) {
      const svg = await scene.evaluate(view => window.cubeCluster.toSVG({ view, size: 960 }), view);
      await render.setContent(`<html><head><style>html,body{margin:0;background:#f3f6fa}svg{display:block}</style></head><body>${svg}</body></html>`);
      await render.screenshot({ path: path.join(output, `${name}.png`) });
    }
  } finally { await browser.close(); }
  console.log('Generated 9 logo previews and 4 model views in docs/images.');
}

build().catch(error => { console.error(error); process.exitCode = 1; });
