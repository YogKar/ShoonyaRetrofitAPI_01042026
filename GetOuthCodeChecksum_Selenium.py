from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from urllib.parse import urlparse, parse_qs
import pyotp
import time
import json
import hashlib
import requests
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
 
# ─── CONFIG ───────────────────────────────────────────────────────────────────
CLIENT_ID   = "FA79490_U"
USER_ID     = "FA79490"
PASSWORD    = "Varnit@61616"
TOTP_SECRET = "6Z3TGU473AZ7ZU63JVAMELPZSI5GIO33" #YOUR base 32 TOTP STRING (From security totp option in trade.shoonya.com ) 
SECRET_CODE = "Q63Xl76my8OMX6yFBrIlIblMRdIBjqN5YpXBiG4M3Onmop5XfbEx33pm2g7I8LP3" #Your api secret code (From API key button in trade.shoonya.com ) 
LOGIN_URL   = f"https://trade.shoonya.com/OAuthlogin/investor-entry-level/login?api_key={CLIENT_ID}&route_to={USER_ID}+s+apikey"  # Change ABC  to your user ID 
TOKEN_URL   = "https://trade.shoonya.com/NorenWClientAPI/GenAcsTok"
# ──────────────────────────────────────────────────────────────────────────────
 
def scan_network_for_code(driver):
    try:
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if message.get("method") == "Network.requestWillBeSent":
                    url = message.get("params", {}).get("request", {}).get("url", "")
                    if "code=" in url:
                        parsed = urlparse(url)
                        code   = parse_qs(parsed.query).get("code", [None])[0]
                        if code:
                            return code
            except Exception:
                continue
    except Exception:
        pass
    return None
 
def fast_fill(driver, element, value):
    element.click()
    time.sleep(0.1)
    element.clear()
    element.send_keys(value)
    time.sleep(0.1)
 
# ── Chrome HEADLESS ────────────────────────────────────────────────────────────
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
 
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait   = WebDriverWait(driver, 30)
 
auth_code = None
 
try:
    # ── Step 1: Login and capture auth code ───────────────────────────────────
    print("Logging in to Shoonya (background)...")
    driver.get(LOGIN_URL)
 
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")))
    time.sleep(1)

    def get_inputs():
        all_inps = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']):not([type='checkbox']):not([type='radio'])")
        return [inp for inp in all_inps if inp.is_displayed()]

    visible_inputs = get_inputs()
    if len(visible_inputs) < 3:
        print(f"[ERROR] Found only {len(visible_inputs)} visible inputs, expected at least 3.")
        driver.save_screenshot("login_page_error.png")
        raise Exception("Login inputs not found")

    print(f"Filling credentials for user {USER_ID}...")
    fast_fill(driver, visible_inputs[0], USER_ID)
    fast_fill(driver, visible_inputs[1], PASSWORD)

    otp_value = pyotp.TOTP(TOTP_SECRET).now()
    fast_fill(driver, visible_inputs[2], otp_value)

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='LOGIN']"))).click()
    print("Credentials submitted. Capturing auth code...")

    start = time.time()
    last_otp_time = start
    while True:
        # Check performance logs
        auth_code = scan_network_for_code(driver)

        # Also check current URL
        if not auth_code:
            current_url = driver.current_url
            if "code=" in current_url:
                parsed = urlparse(current_url)
                auth_code = parse_qs(parsed.query).get("code", [None])[0]
                if auth_code:
                    print(f"Auth Code captured from current URL: {auth_code}")

        if auth_code:
            print(f"Auth Code Captured: {auth_code}")
            break

        # Check for error messages on page
        try:
            err_msg = driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert-danger")
            if err_msg and any(e.is_displayed() for e in err_msg):
                print(f"[PAGE ERROR] {err_msg[0].text}")
        except:
            pass

        if time.time() - start > 120: # 2 minutes timeout
            print("[TIMEOUT] Could not capture auth code after 120 seconds.")
            driver.save_screenshot("timeout_screenshot.png")
            break

        time.sleep(1)
 
except (InvalidSessionIdException, WebDriverException) as e:
    print(f"[ERROR] Browser issue: {e}")
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    try:
        driver.quit()
    except Exception:
        pass
 
# ── Step 2: Generate checksum ──────────────────────────────────────────────────
if auth_code:
    checksum = hashlib.sha256((CLIENT_ID + SECRET_CODE + auth_code).encode()).hexdigest()
    print(f"Checksum: {checksum}")
 
    # ── Step 3: Call GenAcsTok API to get access token ─────────────────────────
    print("\nRequesting access token...")
 
    payload  = f'jData={{"code":"{auth_code}","checksum":"{checksum}"}}'
    headers  = {"Authorization": f"Bearer {checksum}"}
 
    response = requests.post(TOKEN_URL, data=payload, headers=headers)
 
    print(f"Status Code: {response.status_code}")
 
    try:
        result = response.json()
        print("\n" + "=" * 50)
        print("API Response:")
        print(json.dumps(result, indent=2))
        print("=" * 50)
 
        # Extract access token if present
        access_token = result.get("ActTok") or result.get("access_token") or result.get("token")
        if access_token:
            print(f"\nAccess Token: {access_token}")
    except Exception:
        print(f"Raw Response: {response.text}")
 
else:
    print("[ERROR] Auth code not captured — skipping API call.")
 

 
