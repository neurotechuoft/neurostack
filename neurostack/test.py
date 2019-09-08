from socketIO_client import SocketIO
import random
import time
import json

def on_retrieve_prediction_results(*args):
    print(args)
    sid = args[0]
    results = args[1]
    uuid, p300, score = results
    print(f'p300: {p300}')
    print(f'score: {score}')

def on_train_results(*args):
    sid = args[0]
    accuracy = args[1]
    print(f'accuracy: {accuracy}')

def print_results(*args):
    print(args[0])

# p300 server running on localhost:8001
socket_client = SocketIO('localhost', 8002)
socket_client.connect()

# uuid = random.randint(0, 1e10)
uuid = None
timestamp = time.time()
p300 = 1
user = "karl"
password = "cui"
email = "e@mail"

args = json.dumps({'uuid': uuid, 'timestamp': timestamp})
socket_client.emit("predict", args, print_results)
socket_client.wait_for_callbacks(seconds=2)

args = json.dumps({'uuid': uuid, 'timestamp': timestamp, 'p300': p300})
socket_client.emit("train", args, print_results)
socket_client.wait_for_callbacks(seconds=2)