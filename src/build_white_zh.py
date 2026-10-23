from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from compose import node

PROGRAM = Path(__file__).resolve().parent
ROOT = PROGRAM.parent
NS = {'s': 'http://www.w3.org/2000/svg'}


def build():
    original = (ROOT / 'logo.svg').read_text(encoding='utf-8').strip()
    english = (ROOT / 'logo-en-white3d.svg').read_text(encoding='utf-8')
    white = english.split('<g id="brand-symbol">', 1)[1].split('</svg>', 1)[0] + '</svg>'
    chinese = (ROOT / 'logo-zh-white.svg').read_text(encoding='utf-8')
    assert chinese.count(original) == 1
    result = chinese.replace(original, white).replace('10号Logo · 像素北科 · 白字 · 加粗', '10号Logo · 像素北科 · 立体白Logo与白字 · 加粗')
    result = result.replace('10号定稿标志保持原图形和配色，右侧为加粗像素文字；背景透明，无外部字体或位图。', '保留10号几何结构，采用与英文版一致的白色材质及灰阶立体明暗，搭配纯白加粗像素中文，背景透明。')
    (ROOT / 'logo-zh-white3d.svg').write_text(result, encoding='utf-8')
    a, b = ET.fromstring(result), ET.fromstring(english)
    assert ET.tostring(a.find('.//s:g[@id="brand-symbol"]', NS)) == ET.tostring(b.find('.//s:g[@id="brand-symbol"]', NS))
    assert ET.tostring(a.find('.//s:g[@id="pixel-wordmark"]', NS)) == ET.tostring(ET.fromstring(chinese).find('.//s:g[@id="pixel-wordmark"]', NS))
    subprocess.run([node(), str(PROGRAM / 'render.cjs'), '--white', '--zh'], check=True)
    image = np.asarray(Image.open(ROOT / 'logo-zh-white3d.png').convert('RGBA'))
    reference = np.asarray(Image.open(ROOT / 'logo-zh-white.png').convert('RGBA'))
    assert image.shape == (800, 3074, 4)
    assert np.array_equal(image[:, :, 3], reference[:, :, 3])
    assert np.array_equal(image[:, :800], np.asarray(Image.open(ROOT / 'logo-en-white3d.png').convert('RGBA'))[:, :800])
    text = image[:, 960:]
    assert np.all(text[:, :, :3][text[:, :, 3] > 250] == 255)
    (PROGRAM / '输出/white-zh-verification.json').write_text(json.dumps({'white_logo_identical_to_english': True, 'chinese_glyphs_unchanged': True, 'transparent': True, 'png_dimensions': [3074, 800]}, indent=2), encoding='utf-8')
    print('Built and verified logo-zh-white3d.svg/png/@2x.png.')


if __name__ == '__main__':
    build()
