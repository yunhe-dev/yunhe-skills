#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31.0",
#     "pillow>=10.0.0",
# ]
# ///
"""
Generate images using Nano Banana BLT API.

Supports both sync and async generation with multiple aspect ratios and resolutions.
"""

import argparse
import os
import sys
import time
import base64
import urllib3
from pathlib import Path
from datetime import datetime
from typing import Optional

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_api_key(provided_key: Optional[str]) -> Optional[str]:
    """Get API key from argument or environment."""
    if provided_key:
        return provided_key
    return os.environ.get("BLT_API_KEY")

def generate_filename(prompt: str) -> str:
    """Generate filename from timestamp and prompt."""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # Extract first 3-4 words from prompt for filename
    words = prompt.split()[:4]
    desc = "-".join(words).lower()
    # Remove special characters
    desc = "".join(c for c in desc if c.isalnum() or c == "-").rstrip("-")
    if len(desc) > 30:
        desc = desc[:30]
    return f"{timestamp}-{desc}.png"

def validate_aspect_ratio(ratio: str) -> bool:
    """Validate aspect ratio."""
    valid_ratios = [
        "4:3", "3:4", "16:9", "9:16", "2:3", "3:2",
        "1:1", "4:5", "5:4", "21:9", "1:4", "4:1",
        "8:1", "1:8"
    ]
    return ratio in valid_ratios

def validate_size(size: str) -> bool:
    """Validate image size."""
    valid_sizes = ["512px", "1K", "2K", "4K"]
    return size in valid_sizes

def make_request(
    prompt: str,
    api_key: str,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    reference_images: Optional[list] = None,
    async_mode: bool = False,
    webhook: Optional[str] = None
) -> dict:
    """Make API request to generate image."""
    import requests
    
    base_url = "https://api.bltcy.ai/v1/images/generations"
    
    # Build URL with query params for async
    url = base_url
    params = {}
    if async_mode:
        params["async"] = "true"
    if webhook:
        params["webhook"] = webhook
    
    if params:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query_string}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini-3.1-flash-image-preview",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "response_format": "url"
    }
    
    # Add reference images if provided
    if reference_images:
        payload["image"] = reference_images
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}", file=sys.stderr)
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def check_task_status(task_id: str, api_key: str) -> dict:
    """Check async task status."""
    import requests
    
    url = f"https://api.bltcy.ai/v1/images/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking task: {e}", file=sys.stderr)
        sys.exit(1)

def download_image(url: str, output_path: Path) -> None:
    """Download image from URL."""
    import requests
    
    try:
        response = requests.get(url, timeout=120, verify=False)
        response.raise_for_status()
        output_path.write_bytes(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}", file=sys.stderr)
        sys.exit(1)

def process_sync_result(result: dict, output_path: Path) -> None:
    """Process synchronous generation result."""
    if "data" in result and result["data"]:
        image_data = result["data"][0]
        
        if "url" in image_data and image_data["url"]:
            print(f"Downloading image from: {image_data['url']}")
            download_image(image_data["url"], output_path)
            print(f"✅ Image saved: {output_path.resolve()}")
        elif "b64_json" in image_data and image_data["b64_json"]:
            # Decode base64
            image_bytes = base64.b64decode(image_data["b64_json"])
            output_path.write_bytes(image_bytes)
            print(f"✅ Image saved: {output_path.resolve()}")
        else:
            print("❌ No image data in response", file=sys.stderr)
            print(f"Response: {result}", file=sys.stderr)
            sys.exit(1)
        
        # Print usage info if available
        if "usage" in result:
            usage = result["usage"]
            print(f"📊 Tokens: {usage.get('total_tokens', 'N/A')} total")
    else:
        print(f"❌ Unexpected response format: {result}", file=sys.stderr)
        sys.exit(1)

def wait_for_async_task(task_id: str, api_key: str, output_path: Path, max_wait: int = 300) -> None:
    """Wait for async task to complete."""
    print(f"⏳ Waiting for async task: {task_id}")
    print(f"   Checking every 5 seconds (max {max_wait}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        result = check_task_status(task_id, api_key)
        
        if "data" not in result:
            print(f"❌ Invalid response: {result}", file=sys.stderr)
            sys.exit(1)
        
        task_data = result["data"]
        status = task_data.get("status", "UNKNOWN")
        
        if status == "SUCCESS":
            print(f"✅ Task completed!")
            # Handle nested data structure: data.data[0].url
            nested_data = task_data.get("data", {})
            if nested_data and "data" in nested_data and nested_data["data"]:
                image_url = nested_data["data"][0].get("url")
                if image_url:
                    print(f"Downloading image...")
                    download_image(image_url, output_path)
                    print(f"✅ Image saved: {output_path.resolve()}")
                    return
            print("❌ No image URL in completed task", file=sys.stderr)
            sys.exit(1)
        
        elif status == "FAILURE":
            fail_reason = task_data.get("fail_reason", "Unknown error")
            print(f"❌ Task failed: {fail_reason}", file=sys.stderr)
            sys.exit(1)
        
        elif status == "IN_PROGRESS":
            progress = task_data.get("progress", "N/A")
            print(f"   Progress: {progress}", end="\r")
            time.sleep(5)
        
        else:
            print(f"   Status: {status}", end="\r")
            time.sleep(5)
    
    print(f"\n⏰ Timeout after {max_wait}s", file=sys.stderr)
    print(f"Task ID: {task_id}", file=sys.stderr)
    print(f"Check later with: --check-task {task_id}", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Nano Banana BLT API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick generation
  %(prog)s -p "一只猫" -o cat.png
  
  # Specific ratio and size
  %(prog)s -p "日落" -r 16:9 -s 4K -o sunset.png
  
  # Async generation
  %(prog)s -p "复杂场景" -r 21:9 -s 4K --async
  
  # Check async task
  %(prog)s --check-task TASK_ID
        """
    )
    
    parser.add_argument("-p", "--prompt", help="Image description/prompt")
    parser.add_argument("-o", "--output", help="Output filename (auto-generated if not provided)")
    parser.add_argument("-r", "--ratio", default="1:1", help="Aspect ratio (default: 1:1)")
    parser.add_argument("-s", "--size", default="1K", choices=["512px", "1K", "2K", "4K"],
                        help="Image size (default: 1K)")
    parser.add_argument("-a", "--async-mode", dest="async_mode", action="store_true", help="Use async mode")
    parser.add_argument("-ref", "--reference", nargs="+", help="Reference image path(s)")
    parser.add_argument("-k", "--api-key", help="API key (or use BLT_API_KEY env)")
    parser.add_argument("--check-task", metavar="TASK_ID", help="Check async task status")
    parser.add_argument("--webhook", help="Webhook URL for async notifications")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = get_api_key(args.api_key)
    if not api_key:
        print("❌ Error: No API key provided.", file=sys.stderr)
        print("   Please either:", file=sys.stderr)
        print("     1. Provide --api-key argument", file=sys.stderr)
        print("     2. Set BLT_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)
    
    # Handle check-task mode
    if args.check_task:
        print(f"🔍 Checking task: {args.check_task}")
        result = check_task_status(args.check_task, api_key)
        print(f"Status: {result}")
        return
    
    # Validate required arguments for generation
    if not args.prompt:
        print("❌ Error: --prompt is required (unless using --check-task)", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # Validate aspect ratio
    if not validate_aspect_ratio(args.ratio):
        print(f"❌ Error: Invalid aspect ratio '{args.ratio}'", file=sys.stderr)
        print("   Valid ratios: 4:3, 3:4, 16:9, 9:16, 2:3, 3:2, 1:1, 4:5, 5:4, 21:9, 1:4, 4:1, 8:1, 1:8", file=sys.stderr)
        sys.exit(1)
    
    # Generate output filename if not provided
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(generate_filename(args.prompt))
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Process reference images if provided
    reference_images = None
    if args.reference:
        reference_images = []
        for ref_path in args.reference:
            if not Path(ref_path).exists():
                print(f"❌ Error: Reference image not found: {ref_path}", file=sys.stderr)
                sys.exit(1)
            # Convert to base64
            with open(ref_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode()
                # Add data URI prefix
                ext = Path(ref_path).suffix.lower()
                mime_type = "image/png" if ext == ".png" else "image/jpeg"
                reference_images.append(f"data:{mime_type};base64,{b64_data}")
        print(f"📎 Loaded {len(reference_images)} reference image(s)")
    
    # Print generation info
    print(f"🎨 Generating image...")
    print(f"   Prompt: {args.prompt[:60]}{'...' if len(args.prompt) > 60 else ''}")
    print(f"   Ratio: {args.ratio}")
    print(f"   Size: {args.size}")
    mode_str = "Async" if args.async_mode else "Sync"
    print(f"   Mode: {mode_str}")
    print(f"   Output: {output_path}")
    print()
    
    # Make request
    result = make_request(
        prompt=args.prompt,
        api_key=api_key,
        aspect_ratio=args.ratio,
        image_size=args.size,
        reference_images=reference_images,
        async_mode=args.async_mode,
        webhook=args.webhook
    )
    
    # Handle result
    if args.async_mode:
        # Async mode: get task ID and wait
        task_id = result.get("task_id") or result.get("data")
        if task_id:
            print(f"📝 Task ID: {task_id}")
            wait_for_async_task(task_id, api_key, output_path)
        else:
            print(f"❌ Unexpected async response: {result}", file=sys.stderr)
            sys.exit(1)
    else:
        # Sync mode: process immediate result
        process_sync_result(result, output_path)

if __name__ == "__main__":
    main()
