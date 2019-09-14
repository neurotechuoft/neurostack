# Neurostack

Streaming brain waves to machine learning services, made easy.

## P300 Service

### Setup

To setup for the Muse:

1. Stream data from the Muse with BlueMuse. Check out how to do that with MuseLSL [here](https://github.com/alexandrebarachant/muse-lsl).
2. Run `python start_muse.py`
3. Connect to the backend with SocketIO, and start sending jobs!

### Training and making predictions

To use, send a job to the backend with parameters and a callback function. To connect to the backend:

```python
from socketIO_client import SocketIO
import time
import json


def callback_function(*args):
    print(args)

# p300 server running on localhost:8002
socket_client = SocketIO('localhost', 8002)
socket_client.connect()
```

To generate a UUID:

```python
# Generate a UUID
socket_client.emit('generate_uuid', None, print_results)
socket_client.wait_for_callbacks(seconds=1)
```

To send a prediction job:

```python
uuid = 'None'             # Universally unique ID for identification
timestamp = time.time()   # Timestamp of data

# Send a prediction job with the data at timestamp
args = json.dumps({
    'uuid': uuid,
    'timestamp': timestamp
})
socket_client.emit("predict", args, callback_function)
socket_client.wait_for_callbacks(seconds=2)
```

To send a training job:

```python
p300 = 1                  # For training: 1 is P300, 0 is no P300

# Send a training job with the data at timestamp
args = json.dumps({
    'uuid': uuid,
    'timestamp': timestamp,
    'p300': p300
})
socket_client.emit("train", args, callback_function)
socket_client.wait_for_callbacks(seconds=2)
```




<!-- **(In development)**

```python
from neurostack import Neurostack
import neurostack.devices as devices

if __name__ == "main":

    neurostack = Neurostack(
        device = devices.OpenBCI(),
        tags = [
            ui_tag,
        ],
        subscribers = [
            mmc_socket_connection,
            p300_socket_connection,
        ]
    )

    neurostack.start()
```

## Documentation

### class **Neurostack** (*device*=devices.OpenBCI, *subscribers* = [], *tags* = [])

### *Parameters*:

***device***: EEG device type to stream from

***subscribers***: WebSockets of subscribers where EEG data will stream to

***tags***: Sources of tags to append to EEG data

### *Functions*

***start()***

Start streaming EEG from device, and publish data to subscribers.

***stop()***

Stop streaming EEG data from device, and stop publishing data to subscribers. Connection to device remains intact, and device is not turned off.

***shutdown()***

Close connection to device, WebSocket connections to publishers, and tag sources. -->
