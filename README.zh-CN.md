# yunhe-skills（中文说明）

> English README: [`README.md`](./README.md)

这是由 **yunhe-dev** 维护的 OpenClaw 实用技能集合。

当前重点是：生图工作流 + X（Twitter）内容封面工作流。

## 已包含技能

### 1）`nano-banana-blt`
基于 BLT 兼容接口的 Nano Banana 生图技能。

**支持能力**
- 文生图
- 多种宽高比（`1:1`、`16:9`、`21:9` 等）
- 多种分辨率（`1K`、`2K`、`4K`、`512px`）
- 同步 / 异步任务轮询
- 可选参考图输入

**主脚本**
- `skills/nano-banana-blt/scripts/generate_image.py`

### 2）`Openclaw-X-article-cover-generator`
用于生成 OpenClaw 主题的 X 文章封面图（固定构图）。

**构图规则**
- 龙虾主体在画面**右侧 1/4**
- 文字区域在画面**左侧 3/4**
- 保持参考图中的龙虾主体形象一致
- 用户要求 5:2 时，用 **21:9** 近似

**主脚本**
- `skills/Openclaw-X-article-cover-generator/scripts/generate_cover.py`

## 环境要求

- Python 3.10+
- `uv`（推荐）
- 环境变量里配置有效 API Key

```bash
export BLT_API_KEY="你的密钥"
```

## 快速开始

```bash
# nano-banana-blt
uv run ./skills/nano-banana-blt/scripts/generate_image.py \
  --prompt "未来城市黄昏天际线" \
  --ratio 16:9 \
  --size 2K \
  --output demo.png
```

```bash
# Openclaw-X-article-cover-generator
uv run ./skills/Openclaw-X-article-cover-generator/scripts/generate_cover.py \
  --title "零门槛上手 OpenClaw" \
  --reference "https://example.com/reference.jpg" \
  --output x-cover.png \
  --size 2K \
  --async-mode
```

## 说明

- 仓库会持续迭代。
- 每个技能目录下有独立文档（`SKILL.md`）。
- 如果打包平台丢失二进制图片，建议优先使用 URL 参考图。
