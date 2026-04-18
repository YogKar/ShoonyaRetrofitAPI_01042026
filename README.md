# NorenRestApiPy Usage Documentation

This library provides a high-level Python interface for the NorenOMS (Finvasia Shoonya) API. It supports session-based login, OAuth header injection, and real-time data via WebSockets.

## 1. Installation

### Quick Setup

Run this single command to download and set up everything in one step:

**Windows (PowerShell):**

```powershell
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/YogKar/ShoonyaRetrofitAPI_01042026/main/install.bat' -OutFile 'install.bat'; .\install.bat"
```

**Linux / macOS / WSL (Bash):**

```bash
curl -sSL https://raw.githubusercontent.com/YogKar/ShoonyaRetrofitAPI_01042026/main/install.sh | bash
```

### Manual Installation

First, install the library dependencies:

```bash
pip install -r requirements.txt
```

Then, install the library using the generated wheel file:

```bash
pip install NorenRestApiPy-0.0.30-py2.py3-none-any.whl
```

---

## 2. Automated Authentication Helpers

Scripts to automate the Shoonya OAuth login process, generate the checksum, and retrieve the `access_token` automatically. These eliminate the need for manual browser-based login.

### Playwright Version (Recommended)
Fast and modern automation. Requires Playwright.
- **File**: `GetOuthCodeChecksum_Playwright.py`
- **Dependencies**: `pip install playwright pyotp requests`, followed by `playwright install chromium`

### Selenium Version
Standard automation using Chrome.
- **File**: `GetOuthCodeChecksum_Selenium.py`
- **Dependencies**: `pip install selenium webdriver-manager pyotp requests`

---

## 3. Initialization

The library can be imported via `api_helper`. You have three class options for initialization:

```python
from api_helper import ShoonyaApiPy, NorenApiPy

# Recommended approach
api = NorenApiPy() 

# Alternatively
api = ShoonyaApiPy()
```

---

## 4. Authentication Variants

You can use either a session-based login or an OAuth header injection.

```python
# Static parameters
cred = {
    'user': 'USER_ID',
    'pwd': 'PASSWORD',
}

token = {
    'token': 'YOUR_ACCESS_TOKEN'
}

# ==============================================================================
# Variant 1: Session based Login (Used to retrofit old code)
# ==============================================================================
ret = api.set_session(
    userid=cred['user'],
    password=cred['pwd'],
    usertoken=token['token']
)

# ==============================================================================
# Variant 2: OAuth Header Injection (Alternative)
# ==============================================================================
# access_token = token['token']
# ret = api.injectOAuthHeader(access_token, cred['user'], cred['user'])
# ==============================================================================
```

---

## 5. WebSocket (Real-time Data)

To receive real-time updates, you must define callbacks and start the websocket.

### Step 1: Define Callbacks

```python
def on_quote_update(message):
    print(f"Tick received: {message}")

def on_order_update(message):
    print(f"Order update: {message}")

def on_open():
    print("Connection established!")
    # Subscribe to tokens after connection
    api.subscribe('NSE|26000', feed_type='t')
```

### Step 2: Start WebSocket

```python
api.start_websocket(
    order_update_callback=on_order_update,
    subscribe_callback=on_quote_update, 
    socket_open_callback=on_open
)
```

## 6. Common API Methods

### Get Account Margins/Limits

```python
limits = api.get_limits()
print(limits)
```
