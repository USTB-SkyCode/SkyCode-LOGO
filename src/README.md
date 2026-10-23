# 10号 Logo 制作程序

根目录放最终成品：10号纯 Logo 的 HTML、SVG、800 和 3200 像素透明 PNG，六款原色Logo加粗文字版，以及新增的立体白Logo配白色英文版。白色立体版提供 SVG、普通 PNG、双倍 PNG；原色六款的双倍 PNG 可通过完整重建重新生成。

## 使用

- 双击 `run.cmd`：核对最终成品并重新生成全部样式合成图，输出到本文件夹的 `输出/`。
- 在 PowerShell 中运行 `./run.ps1 -Rebuild`：依据根目录的10号 SVG 和本文件夹字体，重新生成纯Logo PNG、六款文字SVG、十二张文字PNG，再生成合成图。
- `输出/预览.html`：查看六款样式、打开旋转预览和最终成品。
- 双击 `run-white.cmd` 或运行 `./run.ps1 -White`：从10号原图和白色英文字标重新生成立体白Logo版，并输出深色PPT背景预览。
- `输出/立体白Logo-预览.html`：在深蓝、深灰、纯黑背景上查看白色立体版和页脚尺寸效果。

根目录的 `logo.svg` 是图形源文件，`logo.html` 是独立的3D旋转页面；完整重建会更新 PNG 和字标，不会覆盖这两个源文件。

## 调用文件名

文件名统一使用小写英文与连字符，同款 SVG 和 PNG 使用相同名称。

| 文件名（省略扩展名） | 内容 |
| --- | --- |
| `logo` | 原色纯Logo，另有 `logo-3200.png` 高清图 |
| `logo-zh-white` | 中文白字 |
| `logo-zh-black` | 中文黑字 |
| `logo-zh-blue` | 中文蓝色渐变字 |
| `logo-en-white` | 英文白字，Logo原色 |
| `logo-en-black` | 英文黑字 |
| `logo-en-blue` | 英文蓝色渐变字 |
| `logo-en-white3d` | 白色立体Logo配白色英文，深色PPT用 |
| `logo-zh-white3d` | 白色立体Logo配白色中文，深色背景用 |

双倍PNG由重建命令生成，后缀为 `@2x.png`。合成图为 `输出/wordmarks.png`，白色版背景预览为 `输出/white-preview.png`。

## 文件

- `compose.py`：核对尺寸、透明背景、文字颜色、字标像素及Logo一致性，生成PNG/JPG合成图与预览页。
- `build_wordmarks.py`：采用此前加粗像素字形构建六款SVG。
- `build_white_wordmark.py`：保留10号结构，以中性白色材质和灰阶明暗制作立体白Logo配白色英文。
- `render.cjs`：从SVG渲染透明PNG。
- `verify.cjs`：检查离线预览、SVG、下载链接与旋转重置功能。
- `build_readme.cjs`：从成品 PNG 与原始三维场景生成根目录 README 使用的九款预览和四角度 PNG，输出至 `docs/images/`。
- `manifest.json`：六款成品名称、尺寸与像素规格。
- `字体/`：像素字体和授权，已独立保存，无需旧版目录。
- `输出/`：最新合成图、网页预览与成品校验。
- `整理记录/`：整理清单与独立重建验证记录。

## 环境

当前电脑自动使用已安装的 Codex Python、Node.js 和浏览器环境。程序与备份目录没有依赖关系；删除根目录的 `备份/` 不会影响成品、旋转页面或重新生成。

如换到其他电脑：安装 Python，执行 `pip install -r requirements.txt`；安装 Node.js，在本目录执行 `npm install playwright sharp`、`npx playwright install chromium`。合成图中文标题使用Windows自带微软雅黑字体。最终SVG和PNG不依赖制作环境或字体文件，HTML可离线旋转查看。
