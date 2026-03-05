---
name: oss-upload
description: 阿里云 OSS 文件上传工具，支持上传文件到阿里云对象存储并生成永久访问链接。使用场景：将本地文件上传到 OSS 并获得可分享的永久 URL。需要配置 ALIYUN_OSS_ACCESS_KEY_ID、ALIYUN_OSS_ACCESS_KEY_SECRET、ALIYUN_OSS_ENDPOINT、ALIYUN_OSS_BUCKET 环境变量。
---

# 阿里云 OSS 文件上传

这个技能提供阿里云 OSS（对象存储服务）的文件上传功能，**默认生成永久访问链接**。

## 快速开始

### 1. 配置环境变量

支持通过 `.env` 文件配置：

**加载优先级**（高→低）：
1. 系统环境变量
2. 项目级配置 `<cwd>/.yunhe-skills/.env`
3. 用户级配置 `~/.yunhe-skills/.env`

```bash
# 用户级配置（推荐）
mkdir -p ~/.yunhe-skills
cat > ~/.yunhe-skills/.env << 'EOF'
ALIYUN_OSS_ACCESS_KEY_ID=your-access-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=your-bucket-name
EOF

# 或直接设置环境变量
export ALIYUN_OSS_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_OSS_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIYUN_OSS_ENDPOINT="https://oss-cn-hangzhou.aliyuncs.com"
export ALIYUN_OSS_BUCKET="your-bucket-name"
```

### 2. 安装依赖

```bash
pip install oss2
```

## 使用方法

### 上传文件（默认生成永久链接）

```bash
python scripts/oss-upload.py upload --file /path/to/local/file.txt
```

**默认行为**：上传后自动设置为公开访问，返回永久链接。

可选参数：
- `--key`：指定 OSS 中的文件名（默认使用本地文件名）
- `--temp`：生成临时访问链接（而非永久链接）
- `--expire`：临时链接有效期（秒，默认 3600）

示例：
```bash
# 上传到指定路径（默认永久链接）
python scripts/oss-upload.py upload --file photo.jpg --key images/photo.jpg

# 生成临时链接
python scripts/oss-upload.py upload --file photo.jpg --temp --expire 7200
```

### 生成访问链接

```bash
# 生成永久链接（默认）
python scripts/oss-upload.py url --key images/photo.jpg

# 生成临时链接
python scripts/oss-upload.py url --key images/photo.jpg --temp --expire 3600
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--file, -f` | 本地文件路径 | - |
| `--key, -k` | OSS 对象名称 | 本地文件名 |
| `--temp, -t` | 生成临时链接 | False（永久链接） |
| `--expire, -e` | 临时链接有效期（秒） | 3600 |

## 注意事项

- **默认生成永久链接**：上传后自动设置为公开读
- 如需临时链接，使用 `--temp` 参数
- Bucket 建议设置为私有，由脚本控制单个文件的访问权限
- 上传大文件时脚本会自动处理，无需额外配置
