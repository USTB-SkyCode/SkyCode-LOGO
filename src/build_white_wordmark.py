from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from compose import node, font

PROGRAM = Path(__file__).resolve().parent
ROOT = PROGRAM.parent
OUT = PROGRAM / '输出'
NAME = 'logo-en-white3d'
NS = {'s': 'http://www.w3.org/2000/svg'}
GRADIENTS = {
    0: ('#c9c9c9', '#ededed'), 1: ('#dedede', '#f7f7f7'),
    2: ('#989898', '#c8c8c8'), 3: ('#b4b4b4', '#dfdfdf'),
    4: ('#8e8e8e', '#bcbcbc'), 5: ('#989898', '#c8c8c8'),
    6: ('#b4b4b4', '#dfdfdf'), 7: ('#bbbbbb', '#e9e9e9'),
    8: ('#d6d6d6', '#f9f9f9'), 9: ('#a0a0a0', '#cbcbcb'),
    10: ('#bbbbbb', '#e9e9e9'), 11: ('#d6d6d6', '#f9f9f9'),
    12: ('#b1b1b1', '#dedede'), 13: ('#cecece', '#f0f0f0'),
    14: ('#bcbcbc', '#e4e4e4'), 15: ('#cacaca', '#f0f0f0'),
    16: ('#a2a2a2', '#cfcfcf'), 17: ('#bdbdbd', '#e7e7e7'),
    18: ('#c4c4c4', '#efefef'), 19: ('#dfdfdf', '#ffffff'),
    20: ('#b5b5b5', '#e3e3e3'), 21: ('#cecece', '#f5f5f5'),
}
SOLIDS = {'#122a55': '#929292', '#39aee4': '#f9f9f9', '#264879': '#d9d9d9',
          '#33a5e3': '#eeeeee', '#3db8f0': '#fcfcfc', '#34a8e7': '#f1f1f1',
          '#284c7f': '#e2e2e2', '#40c1fc': '#ffffff'}


def build():
    original = (ROOT / 'logo.svg').read_text(encoding='utf-8').strip()
    white = original
    for index, colors in GRADIENTS.items():
        pattern = rf'(<linearGradient id="g{index}"[^>]*>)(.*?)(</linearGradient>)'

        def gradient(match):
            stops = iter(colors)
            content = re.sub(r'stop-color="#[0-9a-fA-F]{6}"', lambda _: f'stop-color="{next(stops)}"', match[2])
            return match[1] + content + match[3]

        white, count = re.subn(pattern, gradient, white)
        assert count == 1, index
    for old, new in SOLIDS.items():
        white = white.replace(f'"{old}"', f'"{new}"')
    white = white.replace('<title>方案 10 · 桥端藏到方块内侧</title>', '<title>10号Logo · 白色材质与立体明暗</title>')
    english = (ROOT / 'logo-en-white.svg').read_text(encoding='utf-8')
    assert english.count(original) == 1
    result = english.replace(original, white)
    result = result.replace('10号Logo · USTB SkyCode · 白字 · 加粗', '10号Logo · USTB SkyCode · 立体白Logo与白字 · 加粗')
    result = result.replace('10号定稿标志保持原图形和配色，右侧为加粗像素文字；背景透明，无外部字体或位图。',
                            '保留10号几何结构，以中性白色材质、亮面、背光面及连接阴影表现立体；搭配纯白加粗像素英文，透明背景，适合深色PPT。')
    target = ROOT / (NAME + '.svg')
    target.write_text(result, encoding='utf-8')
    source_tree, white_tree = ET.fromstring(original), ET.fromstring(white)
    assert [p.attrib['points'] for p in source_tree.findall('.//s:polygon', NS)] == [p.attrib['points'] for p in white_tree.findall('.//s:polygon', NS)]
    assert [p.attrib['d'] for p in source_tree.findall('.//s:clipPath/s:path', NS)] == [p.attrib['d'] for p in white_tree.findall('.//s:clipPath/s:path', NS)]
    assert [p.attrib.get('fill-opacity') for p in source_tree.findall('.//s:polygon', NS)] == [p.attrib.get('fill-opacity') for p in white_tree.findall('.//s:polygon', NS)]
    assert ET.tostring(ET.fromstring(english).find('.//s:g[@id="pixel-wordmark"]', NS)) == ET.tostring(ET.fromstring(result).find('.//s:g[@id="pixel-wordmark"]', NS))
    subprocess.run([node(), str(PROGRAM / 'render.cjs'), '--white'], check=True)
    verify()
    preview()


def verify():
    image = Image.open(ROOT / (NAME + '.png')).convert('RGBA')
    assert image.size == (4262, 800)
    assert Image.open(ROOT / (NAME + '@2x.png')).size == (8524, 1600)
    array = np.asarray(image)
    visible = array[:, :, :3][array[:, :, 3] > 250]
    assert np.all(visible[:, 0] == visible[:, 1]) and np.all(visible[:, 1] == visible[:, 2])
    source_alpha = np.asarray(Image.open(ROOT / 'logo-en-white.png').convert('RGBA'))[:, :, 3]
    assert np.array_equal(array[:, :, 3], source_alpha)
    text = array[:, 960:]
    assert np.all(text[:, :, :3][text[:, :, 3] > 250] == 255)
    logo = array[:, :800]
    values = logo[:, :, 0][logo[:, :, 3] > 250]
    assert values.max() == 255 and values.max() - values.min() > 90
    assert image.getpixel((0, 0))[3] == 0
    report = {'geometry_and_bridge_opacity_preserved': True, 'identical_alpha_silhouette': True,
              'english_pixels_unchanged_and_pure_white': True, 'neutral_grayscale_material': True,
              'logo_shading_range': [int(values.min()), int(values.max())], 'transparent_background': True,
              'png_size': list(image.size), 'double_resolution_size': [8524, 1600],
              'files': {NAME + suffix: hashlib.sha256((ROOT / (NAME + suffix)).read_bytes()).hexdigest() for suffix in ['.svg', '.png', '@2x.png']}}
    OUT.mkdir(exist_ok=True)
    (OUT / '立体白Logo-验证.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


def place(board, logo, x, y, width):
    height = round(width * logo.height / logo.width)
    board.paste(logo.resize((width, height), Image.Resampling.LANCZOS), (x, y), logo.resize((width, height), Image.Resampling.LANCZOS))


def preview():
    high = ROOT / (NAME + '@2x.png')
    logo = Image.open(high if high.exists() else ROOT / (NAME + '.png')).convert('RGBA')
    board = Image.new('RGB', (1920, 1440), '#0c1017')
    draw = ImageDraw.Draw(board)
    draw.text((72, 42), '白色立体标志 · 深色 PPT 使用预览', font=font(40), fill='#ffffff')
    draw.text((72, 104), '保留 10 号结构与加粗像素字形，以白色材质的明暗呈现立体感', font=font(25), fill='#aab4c2')
    for index, (color, label) in enumerate([('#151d2c', '深蓝背景'), ('#242424', '深灰背景'), ('#000000', '纯黑背景')]):
        y = 173 + index * 310
        draw.rounded_rectangle((52, y, 1868, y + 288), radius=18, fill=color)
        draw.text((80, y + 18), label, font=font(22), fill='#9da8b8')
        place(board, logo, 260, y + 12, 1400)
    draw.rounded_rectangle((52, 1135, 1868, 1388), radius=18, fill='#141a25')
    draw.text((80, 1160), '页脚缩小效果', font=font(22), fill='#9da8b8')
    draw.text((80, 1220), 'PPT 内容区域', font=font(38), fill='#e8edf5')
    draw.line((80, 1295, 1840, 1295), fill='#303949', width=1)
    place(board, logo, 1400, 1308, 400)
    board.save(OUT / 'white-preview.png', optimize=True)
    name = html.escape(NAME, quote=True)
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>白色立体Logo · PPT</title><style>
*{box-sizing:border-box}body{background:#0c1017;color:#fff;margin:24px;font-family:"Microsoft YaHei",sans-serif}a{color:#c9d9f5}header{max-width:1280px;margin:auto}section{max-width:1280px;margin:24px auto;padding:24px;border-radius:12px}section img{width:100%;display:block}h1{font-size:28px}p{line-height:1.7}.navy{background:#151d2c}.gray{background:#242424}.black{background:#000}.footer{background:#141a25;display:flex;justify-content:flex-end}.footer img{width:360px;max-width:100%}
</style></head><body><header><h1>白色立体Logo · USTB SkyCode</h1><p>高光面接近纯白，侧面和下层保留灰阶阴影。以下背景仅用于展示，成品均为透明背景。</p><p><a href="../../__NAME__.svg" download>SVG 矢量</a> · <a href="../../__NAME__.png" download>透明 PNG</a> · <a href="../../__NAME__@2x.png" download>双倍高清 PNG</a></p></header><section class="navy"><img src="../../__NAME__.png" alt="深蓝背景白色Logo"></section><section class="gray"><img src="../../__NAME__.png" alt="深灰背景白色Logo"></section><section class="black"><img src="../../__NAME__.png" alt="纯黑背景白色Logo"></section><section class="footer"><img src="../../__NAME__.png" alt="页脚尺寸白色Logo"></section></body></html>'''
    if not (ROOT / (NAME + '@2x.png')).exists():
        page = page.replace(' · <a href="../../__NAME__@2x.png" download>双倍高清 PNG</a>', '')
    (OUT / '立体白Logo-预览.html').write_text(page.replace('__NAME__', name), encoding='utf-8')
    print('Created white 3D logo with white English, transparent SVG/PNG and dark-background preview.')


if __name__ == '__main__':
    build()
