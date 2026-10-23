from pathlib import Path
import html
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROGRAM = Path(__file__).resolve().parent
ROOT = PROGRAM.parent
FONT = PROGRAM / '字体/fusion-pixel-12px-proportional-zh_hans.ttf'
CELL, PIXEL, TEXT_X = 36, 54, 960
LANGUAGES = [('中文', 'zh', '像素北科', 3), ('英文', 'en', 'USTB SkyCode', 1)]
COLORS = [('白字', 'white', '#ffffff'), ('黑字', 'black', '#000000'), ('蓝字渐变', 'blue', 'url(#wordmark-blue)')]


def glyphs(text, tracking):
    font = ImageFont.truetype(str(FONT), 12)
    result, pen = [], 0
    for character in text:
        bitmap = Image.new('L', (24, 24))
        ImageDraw.Draw(bitmap).text((0, 0), character, font=font, fill=255)
        array = np.asarray(bitmap)
        assert set(np.unique(array)).issubset({0, 255})
        ys, xs = np.where(array == 255)
        result.append({'char': character, 'points': [(pen + int(x), int(y)) for y, x in zip(ys, xs)]})
        pen += round(font.getlength(character)) + tracking
    points = [p for glyph in result for p in glyph['points']]
    left, top = min(x for x, y in points), min(y for x, y in points)
    columns, rows = max(x for x, y in points) + 1 - left, max(y for x, y in points) + 1 - top
    for glyph in result:
        glyph['points'] = [(x - left, y - top) for x, y in glyph['points']]
    return result, columns, rows


def build():
    logo = (ROOT / 'logo.svg').read_text(encoding='utf-8').strip()
    array = np.asarray(Image.open(ROOT / 'logo.png').convert('RGBA'), dtype=float)
    ys, _ = np.where(array[:, :, 3] > 250)
    palette = []
    for t in [0, .16, .35, .53, .7, .85, 1]:
        y = round(ys.min() + (ys.max() - ys.min()) * (.04 + .92 * t))
        band = array[max(0, y - 12):min(800, y + 13)]
        rgb = np.rint(band[:, :, :3][band[:, :, 3] > 250].mean(axis=0)).astype(int)
        palette.append((t, '#' + ''.join(f'{channel:02x}' for channel in rgb)))
    manifest = []
    for language_name, language, text, tracking in LANGUAGES:
        letters, columns, rows = glyphs(text, tracking)
        y0 = int((800 - rows * CELL) / 2) - 9
        text_height = rows * CELL + 18
        width = TEXT_X + columns * CELL + 18 + 80
        for color_name, color, fill in COLORS:
            name = f'logo-{language}-{color}.svg'
            gradient = f'<linearGradient id="wordmark-blue" gradientUnits="userSpaceOnUse" x1="0" y1="{y0}" x2="0" y2="{y0 + text_height}">' + ''.join(f'<stop offset="{t}" stop-color="{c}"/>' for t, c in palette) + '</linearGradient>'
            pixels = []
            for i, glyph in enumerate(letters):
                if not glyph['points']:
                    continue
                pixels.append(f'<g id="glyph-{i}" data-character="{html.escape(glyph["char"], quote=True)}">')
                pixels.extend(f'<rect x="{TEXT_X + x * CELL}" y="{y0 + y * CELL}" width="54" height="54"/>' for x, y in glyph['points'])
                pixels.append('</g>')
            svg = '\n'.join([
                '<?xml version="1.0" encoding="UTF-8"?>',
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="800" viewBox="0 0 {width} 800" role="img" aria-labelledby="lockup-title">',
                f'<title id="lockup-title">10号Logo · {html.escape(text)} · {color_name} · 加粗</title>',
                '<desc>10号定稿标志保持原图形和配色，右侧为加粗像素文字；背景透明，无外部字体或位图。</desc>',
                f'<defs>{gradient}</defs>' if color == 'blue' else '<defs/>',
                f'<g id="brand-symbol">{logo}</g>',
                f'<g id="pixel-wordmark" fill="{fill}" shape-rendering="crispEdges" aria-label="{html.escape(text, quote=True)}">',
                *pixels, '</g>', '</svg>', '',
            ])
            (ROOT / name).write_text(svg, encoding='utf-8')
            manifest.append({'language': language, 'language_name': language_name, 'text': text,
                             'color': color, 'color_name': color_name, 'svg': name, 'width': width, 'height': 800,
                             'text_bounds': [TEXT_X, y0, columns * CELL + 18, text_height],
                             'pixel_size': PIXEL, 'pixel_pitch': CELL,
                             'pixel_count': sum(len(g['points']) for g in letters)})
    (PROGRAM / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Built 6 vector wordmarks.')


if __name__ == '__main__':
    build()
