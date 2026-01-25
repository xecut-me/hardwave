from secret import BACKDOOR_WS_URL, BACKDOOR_WS_AUTH
from websockets.sync.client import connect
import json

ws = connect(BACKDOOR_WS_URL)

ws.recv()
ws.send('{"type": "auth", "access_token": "' + BACKDOOR_WS_AUTH + '"}')
ws.recv()
ws.send('{"id": 1, "type": "subscribe_events", "event_type": "state_changed"}')
ws.recv()

while True:
    try:
        data = json.loads(ws.recv())["event"]["data"]["new_state"]
        print(data["entity_id"], data["state"])
    except Exception as e:
        print(e)