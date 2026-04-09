import os, sys
# Add the current directory and the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_helper import ShoonyaApiPy, NorenApiPy
import logging
import time

# sample
logging.basicConfig(level=logging.DEBUG)

# flag to tell us if the websocket is open
socket_opened = False


# application callbacks
def event_handler_order_update(message):
    print("order event: " + str(message))


SYMBOLDICT = {}


def event_handler_quote_update(message):
    global SYMBOLDICT
    # e   Exchange
    # tk  Token
    # lp  LTP
    # pc  Percentage change
    # v   volume
    # o   Open price
    # h   High price
    # l   Low price
    # c   Close price
    # ap  Average trade price

    print("quote event: {0}".format(time.strftime('%d-%m-%Y %H:%M:%S')) + str(message))

    key = message['e'] + '|' + message['tk']

    if key in SYMBOLDICT:
        symbol_info = SYMBOLDICT[key]
        symbol_info.update(message)
        SYMBOLDICT[key] = symbol_info
    else:
        SYMBOLDICT[key] = message

    print(SYMBOLDICT[key])


def open_callback():
    global socket_opened
    socket_opened = True
    print('app is connected')

    api.subscribe('NSE|26000', feed_type='t')
    # api.subscribe(['NSE|22', 'BSE|522032'])


# end of callbacks



# start of our program
# api = ShoonyaApiPy()
api = NorenApiPy()

# Static parameters (Replacing YAML file reading)
cred = {
    'user': 'USER_ID',
    'pwd': 'PASSWORD',
}

token = {
    'token': 'YOUR_ACCESS_TOKEN'
}


# ==============================================================================
# Variant 1: Session based Login
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

print(api.get_limits())

if ret != None:
    ret = api.start_websocket(order_update_callback=event_handler_order_update,
                              subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback)

    while True:
        if socket_opened:
            print('q => quit')
            prompt1 = input('what shall we do? ').lower()
            print('Fin') 
            break
        else:
            time.sleep(0.1)  # Avoid high CPU usage while waiting
            continue
