# Neurostack

Streaming brain waves to machine learning services, made easy.

## P300 Service

### Command Line Interface

To run neurostack from the command line, use ```python neurostack.py```.

It takes two arguments:

> `--address`: ip: port to run Neurostack client on. The default is localhost:8002.  
`--server_address`: ip: port for Neurostack server to connect to.

Example Usage: 

>```python neurostack.py --server_address localhost:8001 --address localhost:8002```

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

### WebSocket API

Below we have each of the callable handles, as well as their required parameters and returned values:

#### generate_uuid
Generate a universally unique identifier.

Parameters:
> None

Returns:
> generated UUID

#### predict
Make a prediction the data at a timestamp.

Parameters:
> `uuid`: UUID of whoever is making a prediction. This will determine which classifier we will load up and use.  
`timestamp`: timestamp of chunk of data

Returns:
> `uuid`: UUID of caller  
`p300`: either True or False, predicting whether there is a P300 ERP  
`score`: a value from 0 to 1 denoting the confidence in the prediction

#### train
Give a training example to the classifier.

Parameters:
> `uuid`: UUID of whoever is making a prediction. This will determine which classifier we will load up and use.  
`timestamp`: timestamp of chunk of data  
`p300`: either True or False, depending on whether there should be a P300 ERP

Returns:
> `uuid`: UUID of caller  
`acc`: accuracy of current classifier. This is either None/null (not enough training samples for training), or a number between 0 and 1.
