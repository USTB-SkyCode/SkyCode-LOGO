from pathlib import Path
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROGRAM = Path(__file__).resolve().parent
ROOT = PROGRAM.parent
OUT = PROGRAM / '输出'


def node():
    bundled = Path(os.environ.get('USERPROFILE', '')) / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    found = str(bundled) if bundled.is_file() else shutil.which('node')
    if not found:
        raise RuntimeError('Node.js is required to regenerate PNGs. See README.md.')
    return found


def verify(manifest):
    ns = {'s': 'http://www.w3.org/2000/svg'}
    source = (ROOT / 'logo.svg').read_text(encoding='utf-8').strip()
    logo = np.asarray(Image.open(ROOT / 'logo.png').convert('RGBA'))
    for item in manifest:
        file = ROOT / item['svg']
        assert source in file.read_text(encoding='utf-8')
        tree = ET.parse(file)
        assert not tree.findall('.//s:image', ns) and not tree.findall('.//s:text', ns)
        pixels = tree.find('.//s:g[@id="pixel-wordmark"]', ns).findall('.//s:rect', ns)
        assert len(pixels) == item['pixel_count']
        assert all(p.attrib['width'] == p.attrib['height'] == '54' for p in pixels)
        im = Image.open(file.with_suffix('.png')).convert('RGBA')
        assert im.size == (item['width'], 800)
        high = file.with_name(file.stem + '@2x.png')
        if high.exists():
            assert Image.open(high).size == (item['width'] * 2, 1600)
        assert np.array_equal(np.asarray(im.crop((0, 0, 800, 800))), logo)
        assert im.getpixel((im.width - 1, 799))[3] == 0
        x, y, w, h = item['text_bounds']
        region = np.asarray(im.crop((x, y, x + w, y + h)))
        opaque = region[:, :, :3][region[:, :, 3] > 250]
        assert len(opaque) > 0
        if item['color'] == 'white':
            assert np.all(opaque == 255)
        elif item['color'] == 'black':
            assert np.all(opaque == 0)
        else:
            top = region[:40, :, :3][region[:40, :, 3] > 250].mean(axis=0)
            bottom = region[-40:, :, :3][region[-40:, :, 3] > 250].mean(axis=0)
            assert top[2] > bottom[2] + 60
    record = {'variants': len(manifest), 'logo_pixels_unchanged': True, 'transparent_pngs': True,
              'pixel_font_and_colors_verified': True,
              'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.iterdir()) if p.is_file()}}
    (OUT / '成品校验.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')


def font(size):
    fontfile = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc'
    if not fontfile.is_file():
        raise RuntimeError('Microsoft YaHei font is required for the comparison sheet labels.')
    return ImageFont.truetype(str(fontfile), size)


def compose(manifest):
    board = Image.new('RGB', (3000, 1900), '#edf3f9')
    draw = ImageDraw.Draw(board)
    draw.text((50, 32), '10号定稿 Logo · 加粗像素字标', font=font(46), fill='#193859')
    draw.text((50, 104), '像素北科 / USTB SkyCode · 白字 / 黑字 / 蓝色渐变字 · Logo 保持原色', font=font(28), fill='#607b96')
    draw.text((70, 170), '中文 · 像素北科', font=font(32), fill='#193859')
    draw.text((1550, 170), '英文 · USTB SkyCode', font=font(32), fill='#193859')
    cards = []
    for col, language in enumerate(['zh', 'en']):
        for row, item in enumerate(m for m in manifest if m['language'] == language):
            x, y = 50 + col * 1480, 245 + row * 530
            dark = item['color'] == 'white'
            draw.rounded_rectangle((x, y, x + 1420, y + 490), radius=22, fill='#17243a' if dark else 'white')
            draw.text((x + 28, y + 22), item['color_name'] + ' · 加粗像素字', font=font(25), fill='#bdcfe2' if dark else '#607b96')
            im = Image.open((ROOT / item['svg']).with_suffix('.png')).convert('RGBA')
            ratio = min(1360 / im.width, 370 / im.height)
            im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.Resampling.LANCZOS)
            board.paste(im, (round(x + 30 + (1360 - im.width) / 2), round(y + 80 + (370 - im.height) / 2)), im)
            name = html.escape(Path(item['svg']).stem, quote=True)
            label = item['text'] + ' · ' + item['color_name']
            high_link = f' · <a href="../../{name}@2x.png" download>双倍高清 PNG</a>' if (ROOT / f'{name}@2x.png').exists() else ''
            cards.append(f'<article class="{item["color"]}"><h2>{label}</h2><div><img src="../../{name}.png" alt="{label}"></div><p><a href="../../{name}.svg" download>SVG</a> · <a href="../../{name}.png" download>PNG</a>{high_link}</p></article>')
    board.save(OUT / 'wordmarks.png', optimize=True)
    board.save(OUT / 'wordmarks.jpg', quality=95, subsampling=0)
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>10号Logo · 全部文字样式</title><style>
*{box-sizing:border-box}body{margin:24px;background:#edf3f9;color:#193859;font-family:"Microsoft YaHei",sans-serif}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}article{background:white;border-radius:14px;overflow:hidden;min-width:0}h2,p{padding:0 18px}h2{font-size:18px}article div{height:240px;padding:24px;display:flex;align-items:center;justify-content:center}.white div{background:#17243a}img{max-width:100%;max-height:100%}a{color:#1866b2}@media(max-width:850px){main{grid-template-columns:1fr}body{margin:16px}article div{height:180px}}
</style></head><body><h1>10号定稿 Logo · 加粗像素字标</h1><p><a href="../../logo.html">旋转预览</a> · <a href="../../logo.svg">纯Logo SVG</a> · <a href="wordmarks.png">全部样式合成图</a></p><main>__CARDS__</main></body></html>'''
    (OUT / '预览.html').write_text(page.replace('__CARDS__', '\n'.join(cards)), encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    if '--rebuild' in sys.argv:
        subprocess.run([node(), str(PROGRAM / 'render.cjs'), '--logo'], check=True)
        subprocess.run([sys.executable, str(PROGRAM / 'build_wordmarks.py')], check=True)
        subprocess.run([node(), str(PROGRAM / 'render.cjs')], check=True)
    manifest = json.loads((PROGRAM / 'manifest.json').read_text(encoding='utf-8'))
    verify(manifest)
    compose(manifest)
    print('Verified 6 variants. Comparison sheet and preview saved to output folder.')


if __name__ == '__main__':
    main()
