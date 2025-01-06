"""Typhur IoT API client."""

import hashlib
import json
import logging
import time
import uuid

from aiohttp import ClientSession, ClientResponse
from sortedcontainers import SortedDict

class TyphurClient:
    """Typhur IoT API client."""

    BASE_URL = "https://api.iot.typhur.com/"
    APP_ID = "ap196c116818d9b452"  # Static?
    APP_KEY = "90cd114bed613d81dafca2aa3ce1b7a8"  # Static?
    APP_VERSION = "2812"  # May eventually change?
    APP_USER_AGENT = "okhttp/4.12.0"
    EMPTY_PAYLOAD = {}

    access_token = None
    # Format: Build.BRAND + " " + Build.MODEL + " " + Build.VERSION.RELEASE
    device_info = None

    def __init__(self, device_info: str, device_sn: str, websession: ClientSession):
        """Initialize the client."""
        self.websession = websession
        self.device_info = device_info
        self.device_sn = device_sn

    async def login(self, email: str, password: str) -> dict:
        """Log in and get an access token."""
        logging.debug("Logging in with %s", email)
        payload = {
            "accountName": email,
            "accountPassword": hashlib.md5(password.encode("utf-8")).digest().hex(),
            "deviceInfo": self.device_info,
        }

        response = await self.request("app/account/login", payload)

        response_log = logging.debug
        if "data" in response and "token" in response["data"]:
            self.access_token = response["data"]["token"]
            logging.info("Logged in successfully")
        else:
            logging.error("Login failed")
            response_log = logging.error

        response_log("Login response: %s", response)

        return response

    async def request(self, path: str, payload: map = None) -> ClientResponse:
        """Make a request to the API."""
        if not payload:
            payload = self.EMPTY_PAYLOAD

        headers = self._build_headers(payload)
        # Try to blend in with the mobile app...
        headers["User-Agent"] = self.APP_USER_AGENT

        response = await self.websession.request(
            "POST", f"{self.BASE_URL}{path}", headers=headers, json=payload
        )

        response_json = await response.json()

        response_log = logging.debug
        if "code" in response_json:
            if response_json["code"] != "0" or response.status != 200:
                logging.error("Request to %s failed: %s", path, response_json)
                response_log = logging.error
        else:
            logging.error("Request to %s was malformed: %s", path, response_json)
            response_log = logging.error

        response_log("Payload: %s", payload)
        response_log("Raw response: %s", response)
        response_log("Response: %s", response_json)

        return response_json

    def _build_headers(self, payload: map) -> dict:
        """Build request headers."""

        headers = {
            "x-appId": self.APP_ID,
            "x-appVersion": self.APP_VERSION,
            "x-deviceSn": self.device_sn,
            "x-nonce": str(uuid.uuid4()).replace("-", ""),
            "x-timestamp": str(int(time.time() * 1000)),
            # These should probably change in the future
            "x-lang": "en_US",
            "x-region": "US",
        }

        if self.access_token:
            headers["x-token"] = self.access_token
        else:
            headers["x-token"] = "none"

        headers["x-sign"] = self._build_signature(headers, payload)

        logging.debug("Headers: %s", headers)
        return headers

    def _build_signature(self, headers: dict, payload: map) -> str:
        """Build custom request signature."""

        string_parts = [self.APP_KEY, "|"]

        sorted_headers = SortedDict(headers)
        for key, value in sorted_headers.items():
            string_parts.append(f"{key}={value};")

        # Remove the last semicolon
        string_parts[-1] = string_parts[-1][:-1]
        string_parts.append("|")
        string_parts.append(json.dumps(payload, separators=(",", ":")))

        # Unclear if this is necessary?
        to_hash = "".join(string_parts).replace("\n", "")
        logging.debug("String to hash: %s", to_hash)

        md5_hash = hashlib.md5(to_hash.encode("utf-8"))
        hex_parts = []
        for byte in md5_hash.digest():
            hex_string = format(byte, "02x")
            if len(hex_string) < 2:
                hex_string = "0" + hex_string
            hex_parts.append(hex_string)

        signature = "".join(hex_parts)
        logging.debug("Signature: %s", signature)

        return signature
