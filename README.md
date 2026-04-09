# NorenRestApiPy Usage Documentation

This library provides a high-level Python interface for the NorenOMS (Finvasia Shoonya) API. It supports session-based login, OAuth header injection, and real-time data via WebSockets.

## 1. Installation

First, install the library dependencies:

```bash
pip install -r requirements.txt
```

Then, install the library using the generated wheel file:

```bash
pip install NorenRestApiPy-0.0.30-py2.py3-none-any.whl
```

---

## 2. Initialization

The library can be imported via `api_helper`. You have three class options for initialization:

```python
from api_helper import ShoonyaApiPy, NorenApiPy

# Recommended approach
api = NorenApiPy() 

# Alternatively
api = ShoonyaApiPy()
```

---

## 3. Authentication Variants

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

## 4. WebSocket (Real-time Data)

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

## 5. Common API Methods

### Get Account Margins/Limits

```python
limits = api.get_limits()
print(limits)
```
