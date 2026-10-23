from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent


def build():
    original = (ROOT / 'logo.html').read_text(encoding='utf-8')
    script = original.split('<script>', 1)[1].split('</script>', 1)[0]
    palette = '''
  const BLUE_PALETTE = structuredClone(PALETTE);
  const WHITE_PALETTE = {
    topUpper: hex('#ffffff'), sideUpperHi: hex('#f0f0f0'), sideUpperLo: hex('#c9c9c9'),
    topLower: hex('#e3e3e3'), sideLowerHi: hex('#e2e2e2'), sideLowerLo: hex('#b2b2b2'),
    fillTint: [0.95, 0.95, 0.95], innerHi: hex('#ededed'), innerLo: hex('#d9d9d9'), innerTop: hex('#ffffff'),
    glassTop: hex('#ffffff'), glassHi: hex('#f6f6f6'), glassLo: hex('#cfcfcf'),
    glassAlpha: 0.48, glassBackdrop: hex('#929292'),
  };
  let theme = window.parent !== window && window.parent.document.documentElement.classList.contains('dark') ? 'dark' : 'light';
  const material = document.getElementById('material');
  Object.assign(PALETTE, theme === 'dark' ? WHITE_PALETTE : BLUE_PALETTE);
  document.documentElement.dataset.theme = theme;
'''
    script = script.replace("  const reducedMotion = window.matchMedia", palette + "\n  const reducedMotion = window.matchMedia", 1)
    script = script.replace("    document.getElementById('error').style.display = 'flex';", "    window.parent.postMessage({ type: 'brand-unavailable' }, window.location.origin);", 1)
    controls = '''
  function updateMaterial() {
    const selected = material.value === 'auto' ? (theme === 'dark' ? 'white' : 'blue') : material.value;
    Object.assign(PALETTE, selected === 'white' ? WHITE_PALETTE : BLUE_PALETTE);
    document.documentElement.dataset.material = selected;
    gl.useProgram(opaqueProg.program);
    for (const [key, value] of Object.entries(PALETTE)) {
      const name = 'u' + key[0].toUpperCase() + key.slice(1);
      if (opaqueProg.u[name]) gl.uniform3fv(opaqueProg.u[name], value);
    }
    gl.useProgram(glassProg.program);
    gl.uniform3fv(glassProg.u.uGlassTop, PALETTE.glassTop);
    gl.uniform3fv(glassProg.u.uGlassHi, PALETTE.glassHi);
    gl.uniform3fv(glassProg.u.uGlassLo, PALETTE.glassLo);
    gl.uniform3fv(glassProg.u.uBackdrop, PALETTE.glassBackdrop);
    requestRender();
  }
  material.addEventListener('change', updateMaterial);
  window.addEventListener('message', (event) => {
    if (event.source !== window.parent || event.origin !== window.location.origin || event.data?.type !== 'brand-theme') return;
    theme = event.data.theme === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.theme = theme;
    updateMaterial();
  });
  canvas.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    window.parent.postMessage({ type: 'brand-unavailable' }, window.location.origin);
  });
  updateMaterial();
  requestAnimationFrame(() => window.parent.postMessage({ type: 'brand-ready' }, window.location.origin));
'''
    assert script.endswith('})();\n')
    script = script[:-len('})();\n')] + controls + '})();\n'
    script = script.replace("(() => {", "(() => {\n  try {", 1)
    script = script[:-len('})();\n')] + "  } catch (error) {\n    window.parent.postMessage({ type: 'brand-unavailable' }, window.location.origin);\n  }\n})();\n"
    script = re.sub(r'^[ \t]*//[^\n]*\n', '', script, flags=re.MULTILINE)
    document = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>像素北科 · 三维Logo</title><style>
:root{color-scheme:light;--text:#344054;--muted:#64748b;--surface:rgba(245,247,251,.92);--border:rgba(30,50,80,.14);--focus:#287fc7}
:root[data-theme="dark"]{color-scheme:dark;--text:#e8edf5;--muted:#a5b3c8;--surface:rgba(30,38,52,.94);--border:rgba(180,205,240,.2);--focus:#82c4f4}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent;color:var(--text);font:12px system-ui,"Microsoft YaHei",sans-serif}canvas{display:block;width:100%;height:calc(100% - 44px);touch-action:none;cursor:grab;outline:none}canvas.dragging{cursor:grabbing}canvas:focus-visible{outline:2px solid var(--focus);outline-offset:-3px}.ui{position:absolute;bottom:4px;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:8px;white-space:nowrap}select,button,summary{font:inherit;color:var(--text);background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:6px 8px;cursor:pointer}select:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid var(--focus);outline-offset:2px}button{display:inline-flex;align-items:center;gap:4px}button svg{width:14px;height:14px}.hint{position:absolute;bottom:46px;width:100%;text-align:center;font-size:11px;color:var(--muted);pointer-events:none;transition:opacity .2s}.hint.faded{opacity:0}details{position:absolute;top:4px;right:4px;max-width:calc(100% - 8px)}summary{width:fit-content;margin-left:auto;list-style:none}summary::-webkit-details-marker{display:none}.lights{display:grid;grid-template-columns:auto minmax(60px,1fr) 30px;gap:8px;align-items:center;border:1px solid var(--border);background:var(--surface);border-radius:10px;padding:10px;margin:6px 0 0;width:248px;max-width:100%}.lights legend{display:none}.lights input{width:100%;margin:0;accent-color:var(--focus)}.lights output{text-align:right}.lights button{grid-column:1/-1;justify-self:end}#export-svg{display:none}
</style></head><body>
<canvas id="scene" tabindex="0" role="img" aria-label="像素北科立体Logo。拖拽旋转，滚轮缩放，方向键旋转，R键或双击重置。"></canvas>
<span id="hint" class="hint">拖拽旋转 · 滚轮缩放</span>
<div class="ui"><select id="material" aria-label="Logo配色"><option value="auto">跟随主题</option><option value="blue">经典蓝</option><option value="white">立体白</option></select><button id="reset" type="button">重置视角</button><button id="export-svg" type="button" hidden>导出SVG</button></div>
<details><summary>光照</summary><fieldset id="lights" class="lights"><legend>光照俯仰角</legend><label for="key-pitch">主光</label><input id="key-pitch" type="range" min="-90" max="90" step="1" value="0" aria-describedby="key-pitch-out"><output id="key-pitch-out" for="key-pitch">0°</output><label for="inner-pitch">内侧光</label><input id="inner-pitch" type="range" min="-90" max="90" step="1" value="0" aria-describedby="inner-pitch-out"><output id="inner-pitch-out" for="inner-pitch">0°</output><button id="lights-reset" type="button">恢复默认光照</button></fieldset></details>
<script>__SCRIPT__</script></body></html>
'''
    (ROOT / 'logo-viewer.html').write_text(document.replace('__SCRIPT__', script), encoding='utf-8')
    print('Built responsive site viewer from the original Logo.html scene.')


if __name__ == '__main__':
    build()
