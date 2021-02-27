from socketIO_client import SocketIO
import random
import time
import json


def print_results(args):
    print(args)


# p300 server running on localhost:8002
socket_client = SocketIO('localhost', 8001)
socket_client.connect()

# initialize handlers
socket_client.on('generate_uuid', print_results)
socket_client.on('train', print_results)
socket_client.on('predict', print_results)
socket_client.on('raw_data', print_results)

uuid = random.randint(0, 1e10)
timestamp = time.time()
p300 = 1

# test generate uuid
socket_client.emit('generate_uuid', None)
socket_client.wait(seconds=1)

# test training
for i in range(10):
    timestamp = time.time()
    # p300 = random.choice([0, 1])
    # data = np.random.rand((20))
    # print(data)
    data = [1,2,3,4]
    args = {'uuid': uuid, 'left':True, "data":data}
    socket_client.emit("left_right_train", args,print_results)
    socket_client.wait(seconds=2)

# test predictions
# for i in range(5):
#     timestamp = time.time()
#
#     args = json.dumps({'uuid': uuid, 'timestamp': timestamp})
#     socket_client.emit("left_right_predict", args, print_results)
#     socket_client.wait_for_callbacks(seconds=1)
#
# # test streaming raw data
# args = json.dumps({'uuid': uuid})
# socket_client.emit("start_streaming_raw_data", args)
# socket_client.wait()
#
# # # test stop streaming raw data
# socket_client.emit("stop_streaming_raw_data", args)
# socket_client.wait(seconds=5)

socket_client.disconnect()
