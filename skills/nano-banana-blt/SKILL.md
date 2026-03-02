---
name: nano-banana-blt
description: Generate images using Nano Banana BLT API (Gemini 3.1 Flash). Supports text-to-image with multiple aspect ratios and resolutions.
---

# Nano Banana BLT Image Generation

Generate images using the BLT API (compatible with Nano Banana/Gemini 3.1 Flash model).

## Features

- **Text-to-Image**: Generate images from text prompts
- **Multiple Aspect Ratios**: 4:3, 16:9, 1:1, 9:16, and more
- **Multiple Resolutions**: 512px, 1K, 2K, 4K
- **Sync & Async**: Support both synchronous and asynchronous generation
- **Reference Images**: Support image-to-image with reference images

## Setup

Set your API key:
```bash
export BLT_API_KEY="your-api-key-here"
```

## Usage

### Quick Generate (Sync)

```bash
# Default 1:1 ratio, 1K resolution
uv run ~/.openclaw/workspace/skills/nano-banana-blt/scripts/generate_image.py \
  --prompt "一只穿着西装的猫在喝咖啡" \
  --output cat-coffee.png

# Specify aspect ratio and resolution
uv run ~/.openclaw/workspace/skills/nano-banana-blt/scripts/generate_image.py \
  --prompt "日落时分的城市天际线" \
  --ratio 16:9 \
  --size 2K \
  --output city-sunset.png
```

### Async Generation (for complex images)

```bash
# Start async task
uv run ~/.openclaw/workspace/skills/nano-banana-blt/scripts/generate_image.py \
  --prompt "超现实主义风格的未来城市" \
  --ratio 21:9 \
  --size 4K \
  --async-mode \
  --output futuristic-city.png

# Check status (if task_id is provided)
uv run ~/.openclaw/workspace/skills/nano-banana-blt/scripts/generate_image.py \
  --check-task TASK_ID
```

### With Reference Image

```bash
uv run ~/.openclaw/workspace/skills/nano-banana-blt/scripts/generate_image.py \
  --prompt "保持风格，换成夜景" \
  --reference original.png \
  --output night-version.png
```

## Parameters

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--prompt` | `-p` | Image description (required) | - |
| `--output` | `-o` | Output filename | timestamp.png |
| `--ratio` | `-r` | Aspect ratio | 1:1 |
| `--size` | `-s` | Image size (512px/1K/2K/4K) | 1K |
| `--async-mode` | `-a` | Use async mode | false |
| `--reference` | `-ref` | Reference image path | - |
| `--api-key` | `-k` | API key (or use BLT_API_KEY env) | - |
| `--check-task` | - | Check async task status | - |

## Aspect Ratios

- `1:1` - Square (default)
- `4:3`, `3:4` - Standard portrait/landscape
- `16:9`, `9:16` - Widescreen/Mobile
- `2:3`, `3:2` - Photo ratios
- `4:5`, `5:4` - Social media
- `21:9` - Ultrawide
- `1:4`, `4:1`, `1:8`, `8:1` - Banners

## Resolution Guide

| Size | Dimensions | Use Case |
|------|------------|----------|
| `512px` | 512x512 | Quick drafts |
| `1K` | ~1024px | Standard quality |
| `2K` | ~2048px | High quality |
| `4K` | ~4096px | Maximum quality |

## Workflow Recommendations

### Fast Iteration (Draft → Final)

1. **Draft**: Use `1K` + `1:1` for quick testing
   ```bash
   uv run ... --prompt "..." --size 1K --ratio 1:1 --output draft.png
   ```

2. **Iterate**: Refine prompt based on results

3. **Final**: Use desired ratio and `4K` for production
   ```bash
   uv run ... --prompt "..." --size 4K --ratio 16:9 --output final.png
   ```

### For Complex Scenes

Use `--async-mode` mode for:
- High resolution (4K)
- Complex prompts
- Multiple reference images
- When you don't need immediate results

## Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| `No API key provided` | Set `BLT_API_KEY` environment variable or use `--api-key` |
| `Invalid aspect ratio` | Use one of the supported ratios (see above) |
| `Task failed` | Check task status with `--check-task TASK_ID` |
| `Rate limited` | Use async mode or wait before retrying |

## OpenClaw 封面图规则（你刚指定的）

当用户要做 OpenClaw/龙虾 Logo 封面图时，遵循以下强约束：

1. **必须先拿到标题文案再生成**
   - 如果用户没有给文字标题：**不要生成**，先追问标题。
2. **构图固定**
   - 龙虾 logo 主体放在画面**右侧 1/4**区域。
   - 文字区域占据画面**左侧 3/4**。
   - 保持参考图里的龙虾 logo 主体形象不变（不改造型）。
3. **比例要求**
   - 用户要求 5:2 时，API 不支持 5:2，使用 **21:9** 作为最接近替代并提示用户。
4. **建议提示词模板（可直接改标题后使用）**
   - `按参考图风格生成 OpenClaw 封面图。保持龙虾 logo 主体形象不变，logo 位于画面右侧 1/4。左侧 3/4 预留清晰文字区，放置标题："<标题文本>"。整体科技感、深色背景、高对比、干净留白、可读性强。`

## API Reference

- **Endpoint**: `https://api.bltcy.ai/v1/images/generations`
- **Async Query**: `GET https://api.bltcy.ai/v1/images/tasks/{task_id}`
- **Model**: `gemini-3.1-flash-image-preview`

## Examples

### Social Media Post (Instagram)
```bash
uv run ... --prompt "产品展示图，极简风格" --ratio 4:5 --size 2K
```

### YouTube Thumbnail
```bash
uv run ... --prompt "吸引眼球的缩略图，明亮色彩" --ratio 16:9 --size 2K
```

### Website Banner
```bash
uv run ... --prompt "科技感横幅，深蓝色背景" --ratio 21:9 --size 4K
```

### Mobile Wallpaper
```bash
uv run ... --prompt "抽象艺术，渐变色彩" --ratio 9:16 --size 2K
```
