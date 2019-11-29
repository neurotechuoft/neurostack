from socketIO_client import SocketIO
import random
import time
import json


def print_results(args):
    print(args)


# p300 server running on localhost:8002
socket_client = SocketIO('localhost', 8002)
socket_client.connect()

# initialize handlers
socket_client.on('uuid', print_results)
socket_client.on('train', print_results)
socket_client.on('predict', print_results)

# uuid = random.randint(0, 1e10)
uuid = 'd6af3d5a-da9f-4199-95d1-750308b0d1aa'
timestamp = time.time()
p300 = 1

# test generate uuid
socket_client.emit('generate_uuid', None)
socket_client.wait(seconds=1)

# test training
for i in range(20):
    timestamp = time.time()
    p300 = random.choice([0, 1])

    args = json.dumps({'uuid': uuid, 'timestamp': timestamp, 'p300': p300})
    socket_client.emit("train", args)
    socket_client.wait(seconds=1)

# test predictions
for i in range(5):
    timestamp = time.time()

    args = json.dumps({'uuid': uuid, 'timestamp': timestamp})
    socket_client.emit("predict", args)
    socket_client.wait(seconds=1)

socket_client.disconnect()
