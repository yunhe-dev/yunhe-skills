#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
#     "urllib3>=2.0.0",
# ]
# ///
"""
Generate images using Nano Banana BLT API (OpenAI SDK compatible).
"""

import argparse
import os
import sys
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional

def get_api_key(provided_key: Optional[str]) -> Optional[str]:
    if provided_key:
        return provided_key
    return os.environ.get("BLT_API_KEY")

def generate_filename(prompt: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    words = prompt.split()[:4]
    desc = "-".join(words).lower()
    desc = "".join(c for c in desc if c.isalnum() or c == "-").rstrip("-")
    if len(desc) > 30:
        desc = desc[:30]
    return f"{timestamp}-{desc}.png"

def validate_aspect_ratio(ratio: str) -> bool:
    valid_ratios = [
        "4:3", "3:4", "16:9", "9:16", "2:3", "3:2",
        "1:1", "4:5", "5:4", "21:9", "1:4", "4:1",
        "8:1", "1:8"
    ]
    return ratio in valid_ratios

def main():
    parser = argparse.ArgumentParser(description="Generate images using BLT API (OpenAI SDK)")
    parser.add_argument("-p", "--prompt", required=True, help="Image description")
    parser.add_argument("-o", "--output", help="Output filename")
    parser.add_argument("-r", "--ratio", default="1:1", help="Aspect ratio")
    parser.add_argument("-s", "--size", default="1K", choices=["512px", "1K", "2K", "4K"])
    parser.add_argument("-a", "--async-mode", action="store_true")
    parser.add_argument("--check-task", help="Check task status")
    args = parser.parse_args()

    api_key = get_api_key(None)
    if not api_key:
        print("❌ Error: Set BLT_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    if args.check_task:
        print(f"Checking task: {args.check_task}")
        return

    if not validate_aspect_ratio(args.ratio):
        print(f"❌ Invalid ratio: {args.ratio}", file=sys.stderr)
        sys.exit(1)

    # Generate output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(generate_filename(args.prompt))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎨 Generating with OpenAI SDK...")
    print(f"   Prompt: {args.prompt[:60]}...")
    print(f"   Ratio: {args.ratio}")
    print(f"   Size: {args.size}")

    try:
        from openai import OpenAI
        
        # Initialize client with BLT base URL
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.blt.ai/v1",
            http_client=None  # Let it use default
        )
        
        # Map size to resolution
        size_map = {
            "512px": "512x512",
            "1K": "1024x1024", 
            "2K": "1024x1536",
            "4K": "1536x1024"
        }
        
        # Call API
        response = client.images.generate(
            model="gemini-3.1-flash-image-preview",
            prompt=args.prompt,
            size=size_map[args.size],
            quality="hd" if args.size == "4K" else "standard",
            n=1,
            response_format="url"
        )
        
        # Download image
        image_url = response.data[0].url
        import requests
        image_data = requests.get(image_url, verify=False).content
        output_path.write_bytes(image_data)
        
        print(f"✅ Image saved: {output_path.resolve()}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
