#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import hashlib
import traceback
from urllib.parse import urlparse, parse_qs

import pyotp
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ──────────────────────────────────────────────────────────────────────────────
# CONFIG (read from environment variables)
# ──────────────────────────────────────────────────────────────────────────────
CLIENT_ID   = "" # Replace abc with your Client _id
USER_ID     = "" # Replace abc  with your User_id
PASSWORD    = "" # Replace abc with your trading Account password
TOTP_SECRET = "" # Replace abc with 32 base string
SECRET_CODE = "" # Replace abc with your secret_code
LOGIN_URL   = f"https://trade.shoonya.com/OAuthlogin/investor-entry-level/login?api_key={CLIENT_ID}&route_to= {USER_ID}" # replace abc with userid
TOKEN_URL   = "https://trade.shoonya.com/NorenWClientAPI/GenAcsTok"


REQUEST_TIMEOUT = 30
AUTH_CAPTURE_TIMEOUT_SEC = 60


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def fail(msg: str, exit_code: int = 1):
    print(f"[ERROR] {msg}")
    raise SystemExit(exit_code)


def ensure_config():
    missing = []
    if not CLIENT_ID:
        missing.append("SHOONYA_CLIENT_ID")
    if not USER_ID:
        missing.append("SHOONYA_USER_ID")
    if not PASSWORD:
        missing.append("SHOONYA_PASSWORD")
    if not TOTP_SECRET:
        missing.append("SHOONYA_TOTP_SECRET")
    if not SECRET_CODE:
        missing.append("SHOONYA_SECRET_CODE")

    if missing:
        fail(
            "Missing required environment variables: " + ", ".join(missing) +
            "\nPlease export them before running the script."
        )


def generate_otp(secret: str) -> str:
    try:
        return pyotp.TOTP(secret).now()
    except Exception as exc:
        fail(f"Failed to generate TOTP. Check SHOONYA_TOTP_SECRET format. Details: {exc}")


def extract_code_from_url(url: str):
    try:
        parsed = urlparse(url)
        return parse_qs(parsed.query).get("code", [None])[0]
    except Exception:
        return None


def safe_json_response(response: requests.Response):
    try:
        return response.json()
    except Exception:
        return None


def get_visible_inputs(page):
    """
    Return visible input locators excluding hidden/checkbox/radio.
    """
    selector = "input:not([type='hidden']):not([type='checkbox']):not([type='radio'])"
    locator = page.locator(selector)
    count = locator.count()
    visible = []

    for i in range(count):
        item = locator.nth(i)
        try:
            if item.is_visible():
                visible.append(item)
        except Exception:
            continue

    return visible


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    ensure_config()

    auth_code_holder = {"code": None}

    def maybe_capture_code(url: str):
        if not url:
            return
        code = extract_code_from_url(url)
        if code:
            auth_code_holder["code"] = code

    browser = None
    context = None
    page = None

    try:
        with sync_playwright() as p:
            # Playwright manages its own browser binaries after "playwright install"
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            # Capture request URLs (network-level)
            page.on("request", lambda request: maybe_capture_code(request.url))

            # Capture top-level/frame navigations too
            page.on("framenavigated", lambda frame: maybe_capture_code(frame.url))

            print("[INFO] Logging in to Shoonya (Playwright headless)...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT * 1000)

            # Wait until password input is available
            page.wait_for_selector("input[type='password']", timeout=30000)

            time.sleep(1)

            visible_inputs = get_visible_inputs(page)
            if len(visible_inputs) < 3:
                fail(
                    f"Expected at least 3 visible inputs (user, password, otp), "
                    f"found {len(visible_inputs)}"
                )

            # Fill login form
            visible_inputs[0].click()
            visible_inputs[0].fill(USER_ID)

            visible_inputs[1].click()
            visible_inputs[1].fill(PASSWORD)

            otp_value = generate_otp(TOTP_SECRET)
            visible_inputs[2].click()
            visible_inputs[2].fill(otp_value)

            # Click LOGIN
            page.locator("//button[normalize-space()='LOGIN']").click()
            print("[INFO] Credentials submitted. Capturing auth code...")

            start = time.time()

            while True:
                # Try current page URL
                maybe_capture_code(page.url)

                if auth_code_holder["code"]:
                    print(f"[INFO] Auth Code: {auth_code_holder['code']}")
                    break

                if time.time() - start > AUTH_CAPTURE_TIMEOUT_SEC:
                    new_otp = generate_otp(TOTP_SECRET)

                    if new_otp != otp_value:
                        # Re-find visible inputs because page DOM may have changed
                        visible_inputs = get_visible_inputs(page)
                        if len(visible_inputs) >= 3:
                            visible_inputs[2].click()
                            visible_inputs[2].fill(new_otp)

                            page.locator("//button[normalize-space()='LOGIN']").click()

                            start = time.time()
                            otp_value = new_otp
                            continue

                    print("[TIMEOUT] Could not capture auth code.")
                    break

                time.sleep(0.5)

            auth_code = auth_code_holder["code"]

            # Browser cleanup before token API call
            context.close()
            browser.close()

    except PlaywrightTimeoutError as e:
        print(f"[ERROR] Playwright timeout: {e}")
        traceback.print_exc()
        auth_code = None
    except Exception as e:
        print(f"[ERROR] Browser/automation issue: {e}")
        traceback.print_exc()
        auth_code = None

    # ── Step 2: Generate checksum ────────────────────────────────────────────
    if auth_code:
        checksum = hashlib.sha256((CLIENT_ID + SECRET_CODE + auth_code).encode()).hexdigest()
        print(f"[INFO] Checksum: {checksum}")

        # ── Step 3: Call GenAcsTok API to get access token ───────────────────
        print("[INFO] Requesting access token...")

        payload = f'jData={{"code":"{auth_code}","checksum":"{checksum}"}}'
        headers = {
            "Authorization": f"Bearer {checksum}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(
                TOKEN_URL,
                data=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )

            print(f"[INFO] Status Code: {response.status_code}")

            result = safe_json_response(response)
            if result is not None:
                print("\n" + "=" * 60)
                print("API Response:")
                print(json.dumps(result, indent=2))
                print("=" * 60)

                access_token = (
                    result.get("ActTok")
                    or result.get("access_token")
                    or result.get("token")
                )

                if access_token:
                    print(f"\n[INFO] Access Token: {access_token}")
                else:
                    print("[WARN] Access token not found in JSON response.")
            else:
                print("[WARN] Non-JSON response received:")
                print(response.text)

        except requests.RequestException as exc:
            print(f"[ERROR] Token request failed: {exc}")
            traceback.print_exc()

    else:
        print("[ERROR] Auth code not captured — skipping API call.")


if __name__ == "__main__":
    main()