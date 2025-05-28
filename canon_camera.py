import base64
import os

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("canon-camera")


class CanonCamera:
    """Canon Camera CCAPI interface"""

    def __init__(self, ip: str = None, port: int = 8080):
        self.ip = ip or os.environ.get("CANON_IP", None)
        self.port = port
        self.base_url = f"http://{self.ip}:{self.port}"

    def _get(self, path: str) -> requests.Response:
        """Execute GET request"""
        url = f"{self.base_url}{path}"
        logger.info(f"GET: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response

    def _put(self, path: str, data: dict) -> requests.Response:
        """Execute PUT request"""
        url = f"{self.base_url}{path}"
        logger.info(f"PUT: {url} <- {data}")
        response = requests.put(url, json=data, timeout=10)
        response.raise_for_status()
        return response

    def get_all_settings(self) -> dict:
        """Get all shooting settings"""
        response = self._get("/ccapi/ver100/shooting/settings")
        return response.json()

    def get_setting(self, setting_name: str) -> dict:
        """Get specific shooting setting"""
        response = self._get(f"/ccapi/ver100/shooting/settings/{setting_name}")
        return response.json()

    def set_setting(self, setting_name: str, value: str) -> dict:
        """Set specific shooting setting"""
        # First get current setting to validate
        current = self.get_setting(setting_name)

        if "ability" in current and value not in current["ability"]:
            raise ValueError(f"Invalid value '{value}' for {setting_name}. "
                             f"Available options: {current['ability']}")

        response = self._put(f"/ccapi/ver100/shooting/settings/{setting_name}",
                             {"value": value})
        response.raise_for_status()

        # Return updated setting info
        return {
            "setting": setting_name,
            "previous_value": current.get("value"),
            "new_value": value,
            "success": True
        }

    def init_live_view(self, liveviewsize="small", cameradisplay="keep"):
        try:
            url = f"{self.base_url}/ccapi/ver100/shooting/liveview/"
            body = {"liveviewsize": liveviewsize, "cameradisplay": cameradisplay}
            res = requests.post(url, json=body)
            return res.status_code
        except Exception as e:
            logger.error(f"Failed to init live view {e}")
            raise

    def get_liveview_image(self) -> str:
        """Get live view image as base64 string"""
        try:
            url = f"{self.base_url}/ccapi/ver100/shooting/liveview/flip"
            logger.info(f"Getting live view: {url}")
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()

            # Convert to base64
            image_data = f"{base64.b64encode(response.content).decode('utf-8')}\n"
            return image_data
        except Exception as e:
            logger.error(f"Failed to get live view: {e}")
            raise
