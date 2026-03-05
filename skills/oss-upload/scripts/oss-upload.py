#!/usr/bin/env python3
"""
阿里云 OSS 文件上传脚本
支持：上传文件、生成临时/永久访问链接
"""
import os
import sys
import argparse
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path

try:
    import oss2
except ImportError:
    print("Error: oss2 library not installed. Run: pip install oss2")
    sys.exit(1)


def _load_env_file(env_path: Path) -> dict[str, str]:
    """加载单个 .env 文件"""
    env = {}
    if not env_path.exists():
        return env
    content = env_path.read_text(encoding="utf-8")
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        env[key] = value
    return env


def _load_env() -> None:
    """加载环境变量，优先级：系统环境变量 > 项目级 > 用户级"""
    home = Path.home()
    cwd = Path.cwd()

    # 用户级：~/.yunhe-skills/.env
    home_env = _load_env_file(home / ".yunhe-skills" / ".env")
    # 项目级：<cwd>/.yunhe-skills/.env
    cwd_env = _load_env_file(cwd / ".yunhe-skills" / ".env")

    # 先加载用户级（低优先级）
    for k, v in home_env.items():
        if k not in os.environ:
            os.environ[k] = v
    # 再加载项目级（高优先级）
    for k, v in cwd_env.items():
        if k not in os.environ:
            os.environ[k] = v


def get_env_or_raise(var_name):
    """获取环境变量，如果不存在则报错"""
    value = os.environ.get(var_name)
    if not value:
        raise ValueError(f"环境变量 {var_name} 未设置")
    return value


def get_oss_bucket():
    """从环境变量获取 OSS 配置并创建 bucket 实例"""
    access_key_id = get_env_or_raise('ALIYUN_OSS_ACCESS_KEY_ID')
    access_key_secret = get_env_or_raise('ALIYUN_OSS_ACCESS_KEY_SECRET')
    endpoint = get_env_or_raise('ALIYUN_OSS_ENDPOINT')
    bucket_name = get_env_or_raise('ALIYUN_OSS_BUCKET')
    
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    return bucket


def upload_file(local_path, oss_key=None, headers=None):
    """
    上传文件到 OSS
    
    Args:
        local_path: 本地文件路径
        oss_key: OSS 中的对象名称（可选，默认使用文件名）
        headers: 自定义请求头（可选）
    
    Returns:
        上传后的 OSS key
    """
    bucket = get_oss_bucket()
    
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"文件不存在: {local_path}")
    
    # 如果没有指定 oss_key，使用文件名
    if not oss_key:
        oss_key = os.path.basename(local_path)
    
    # 自动检测 Content-Type
    content_type, _ = mimetypes.guess_type(local_path)
    if content_type:
        # 对于文本类文件，添加 charset=utf-8
        if content_type.startswith('text/') or content_type in ['application/json', 'application/javascript', 'application/xml']:
            content_type = f"{content_type};charset=utf-8"
        if not headers:
            headers = {'Content-Type': content_type}
        else:
            headers.setdefault('Content-Type', content_type)
    
    # 上传文件
    if headers:
        bucket.put_object_from_file(oss_key, local_path, headers=headers)
    else:
        bucket.put_object_from_file(oss_key, local_path)
    
    return oss_key


def set_public_acl(oss_key):
    """
    设置对象为公开可读
    
    Args:
        oss_key: OSS 对象名称
    
    Returns:
        公开访问 URL
    """
    bucket = get_oss_bucket()
    bucket.put_object_acl(oss_key, oss2.OBJECT_ACL_PUBLIC_READ)
    
    # 构建永久公开链接
    endpoint = get_env_or_raise('ALIYUN_OSS_ENDPOINT')
    bucket_name = get_env_or_raise('ALIYUN_OSS_BUCKET')
    
    # 移除 https:// 前缀
    endpoint_clean = endpoint.replace('https://', '').replace('http://', '')
    public_url = f"https://{bucket_name}.{endpoint_clean}/{oss_key}"
    
    return public_url


def generate_signed_url(oss_key, expire_seconds=3600):
    """
    生成带签名的临时访问链接
    
    Args:
        oss_key: OSS 对象名称
        expire_seconds: 链接有效期（秒），默认 1 小时
    
    Returns:
        临时访问 URL
    """
    bucket = get_oss_bucket()
    
    # 检查对象是否存在
    if not bucket.object_exists(oss_key):
        raise FileNotFoundError(f"OSS 对象不存在: {oss_key}")
    
    # 生成签名 URL
    url = bucket.sign_url('GET', oss_key, expire_seconds)
    return url


def main():
    _load_env()  # 加载 .env 文件
    parser = argparse.ArgumentParser(description='阿里云 OSS 文件上传工具')
    parser.add_argument('command', choices=['upload', 'url'], help='操作命令')
    parser.add_argument('--file', '-f', help='本地文件路径（upload 命令必需）')
    parser.add_argument('--key', '-k', help='OSS 对象名称（可选，默认使用文件名）')
    parser.add_argument('--expire', '-e', type=int, default=3600,
                        help='临时链接有效期（秒），默认 3600 秒（1小时）')
    parser.add_argument('--temp', '-t', action='store_true',
                        help='生成临时访问链接（默认生成永久链接）')

    args = parser.parse_args()

    try:
        if args.command == 'upload':
            if not args.file:
                print("Error: upload 命令需要 --file 参数")
                sys.exit(1)

            oss_key = upload_file(args.file, args.key)
            print(f"上传成功: {oss_key}")

            if args.temp:
                # 生成临时访问链接
                url = generate_signed_url(oss_key, args.expire)
                print(f"临时访问链接（{args.expire}秒后过期）:")
                print(url)
            else:
                # 默认：设置为公开并生成永久链接
                public_url = set_public_acl(oss_key)
                print(f"✅ 永久链接:")
                print(public_url)

        elif args.command == 'url':
            if not args.key:
                print("Error: url 命令需要 --key 参数")
                sys.exit(1)

            if args.temp:
                url = generate_signed_url(args.key, args.expire)
                print(f"临时访问链接（{args.expire}秒后过期）:")
                print(url)
            else:
                # 默认：设置为公开并生成永久链接
                public_url = set_public_acl(args.key)
                print(f"✅ 永久链接:")
                print(public_url)
            
    except ValueError as e:
        print(f"配置错误: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"操作失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
