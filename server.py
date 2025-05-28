#!/usr/bin/env python3
"""
Canon Camera MCP Server with FastMCP Streamable HTTP Transport
A minimal MCP server for controlling Canon cameras via CCAPI using FastMCP
"""
import io
import json
import os
import base64
import typing

import requests
import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP, Image

from PIL import Image as PILImage

from canon_camera import CanonCamera

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("canon-camera-mcp")





def compress_image_to_target_size(pil_img, target_size_mb=1, format="JPEG"):
    """
    Compress a PIL image to approximately the target size in MB.
    < Written by ChatGPT >

    Args:
        pil_img: PIL Image object
        target_size_mb: Target size in megabytes (default: 1)
        format: Image format ("JPEG" or "PNG")

    Returns:
        bytes: Compressed image data
    """
    target_size_bytes = target_size_mb * 1024 * 1024  # Convert MB to bytes

    # Convert to RGB if saving as JPEG (JPEG doesn't support transparency)
    if format.upper() == "JPEG" and pil_img.mode in ("RGBA", "P"):
        pil_img = pil_img.convert("RGB")

    # Start with high quality and reduce if needed
    quality = 95
    min_quality = 10

    while quality >= min_quality:
        img_byte_arr = io.BytesIO()

        if format.upper() == "JPEG":
            pil_img.save(img_byte_arr, format="JPEG", quality=quality, optimize=True)
        else:
            # For PNG, use optimization
            pil_img.save(img_byte_arr, format="PNG", optimize=True)

        img_size = img_byte_arr.tell()

        if img_size <= target_size_bytes:
            return img_byte_arr.getvalue()

        # Reduce quality for next iteration
        quality -= 5

    # If still too large, resize the image
    return resize_and_compress_image(pil_img, target_size_bytes, format)


def resize_and_compress_image(pil_img, target_size_bytes, format="JPEG"):
    """
    Resize and compress image if quality reduction alone isn't enough.
    """
    original_width, original_height = pil_img.size
    scale_factor = 0.9  # Start by reducing size by 10%
    img_byte_arr = None

    while scale_factor > 0.1:  # Don't go below 10% of original size
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        resized_img = pil_img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

        # Try with medium quality after resizing
        img_byte_arr = io.BytesIO()

        if format.upper() == "JPEG":
            resized_img.save(img_byte_arr, format="JPEG", quality=75, optimize=True)
        else:
            resized_img.save(img_byte_arr, format="PNG", optimize=True)

        img_size = img_byte_arr.tell()

        if img_size <= target_size_bytes:
            return img_byte_arr.getvalue()

        scale_factor -= 0.1

    # If still too large, return the smallest version
    return img_byte_arr.getvalue()





# Initialize camera and FastMCP server
camera = CanonCamera()

mcp = FastMCP("Canon Camera Controller")


@mcp.tool()
def get_camera_settings(setting: Literal["all", "av", "tv", "iso"]) -> str:
    """
    Get all camera shooting settings or a specific setting

    Args:
        setting: Specific setting to get (av, tv, iso, shootingmodedial) or 'all' for all settings
    """
    try:
        if setting == "all":
            result = camera.get_all_settings()
            # Filter the result to only the keys
            keys_to_keep = ["av", "tv", "iso", "shootingmodedial"]
            result = {key: result[key] for key in keys_to_keep if key in result}

        else:
            valid_settings = ["av", "tv", "iso", "shootingmodedial"]
            if setting not in valid_settings:
                raise ValueError(f"Invalid setting '{setting}'. Valid options: {valid_settings}")

            result = camera.get_setting(setting)
            result["setting_name"] = setting

        res = json.dumps(result, indent=2)
        return res

    except requests.exceptions.RequestException as e:
        logger.error(f"Camera communication error: {e}")
        return json.dumps({
            "success": False,
            "error": "camera_communication_error",
            "message": f"Failed to communicate with camera: {str(e)}"
        }, indent=2)

    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return json.dumps({
            "success": False,
            "error": "invalid_parameter",
            "message": str(e)
        }, indent=2)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return json.dumps({
            "success": False,
            "error": "internal_error",
            "message": f"Unexpected error: {str(e)}"
        }, indent=2)


@mcp.tool()
def set_camera_setting(setting: str, value: str) -> str:
    """
    Set a camera shooting setting (aperture, shutter speed, or ISO)

    Args:
        setting: Setting to change (av, tv, iso)
        value: Value to set (must be from the setting's ability list)
    """
    try:
        valid_settings = ["av", "tv", "iso"]
        if setting not in valid_settings:
            raise ValueError(f"Invalid setting '{setting}'. Valid options: {valid_settings}")

        if not value:
            raise ValueError("Value is required")

        result = camera.set_setting(setting, value)
        return json.dumps(result, indent=2)

    except requests.exceptions.RequestException as e:
        logger.error(f"Camera communication error: {e}")
        return json.dumps({
            "success": False,
            "error": "camera_communication_error",
            "message": f"Failed to communicate with camera: {str(e)}"
        }, indent=2)

    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return json.dumps({
            "success": False,
            "error": "invalid_parameter",
            "message": str(e)
        }, indent=2)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return json.dumps({
            "success": False,
            "error": "internal_error",
            "message": f"Unexpected error: {str(e)}"
        }, indent=2)


@mcp.tool()
def get_liveview() -> typing.Union[Image, str]:
    """
    Get current live view image from camera. Use this to cross check if the new settings have actually worked.

    Returns an image.
    """
    try:
        image_data_b64 = camera.get_liveview_image()
        image_data_bytes = base64.b64decode(image_data_b64)
        pil_img = PILImage.open(io.BytesIO(image_data_bytes))

        # Compress the image to ~1MB
        compressed_img_bytes = compress_image_to_target_size(pil_img, target_size_mb=1, format="JPEG")
        img = Image(data=compressed_img_bytes, format="jpeg")
        img_content = img.to_image_content()
        logger.info(f"Image content: {img_content}")
        logger.info(f"Compressed image size: {len(compressed_img_bytes) / (1024 * 1024):.2f} MB")

        return img

    except requests.exceptions.RequestException as e:
        logger.error(f"Camera communication error: {e}")
        return json.dumps({
            "success": False,
            "error": "camera_communication_error",
            "message": f"Failed to communicate with camera: {str(e)}"
        }, indent=2)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return json.dumps({
            "success": False,
            "error": "internal_error",
            "message": f"Unexpected error: {str(e)}"
        }, indent=2)


def main():
    """Main entry point"""
    # Configuration
    host = os.environ.get("MCP_HOST", "localhost")
    port = int(os.environ.get("MCP_PORT", "3001"))

    logger.info(f"Starting Canon Camera MCP Server on {host}:{port}")
    logger.info(f"Canon Camera IP: {camera.ip}:{camera.port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/")

    # Test camera connection on startup
    try:
        camera.get_all_settings()
        camera.init_live_view()
        logger.info("✓ Camera connection successful")
    except Exception as e:
        logger.warning(f"⚠ Camera connection failed: {e}")
        logger.info("Server will start anyway - camera connection will be retried on requests")

    # Run server with streamable HTTP transport
    # mcp.run(transport="streamable-http")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()


