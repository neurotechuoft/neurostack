# Neurostack

Streaming brain waves to machine learning services, made easy.

## Installation

Neurostack runs in Python 3.6. We recommend working in a virtual environment (see [Conda](https://www.anaconda.com/) or [venv](https://docs.python.org/3/library/venv.html)).

For users who want to connect to the server that is already running in the cloud, or for users who do not need machine learning services (Such as those who only want to stream raw EEG data from the headset) only `requirements.txt` is needed.
To install dependencies for the Neurostack client, run
```bash
pip install -r requirements.txt
```

For users who wish to use their own server (instead of the one already running in the cloud), `server_requirements.txt` are also needed.
To install these dependencies for the Neurostack server, run
```bash
pip install -r server_requirements.txt
```

## Usage

To run the Neurostack server, use `python start_server.py`. It will run on localhost:8001.

__Neurostack server is currently running on `neurostack.neurotechuoft.com` on port 8001, so if you do not wish to run the server locally, you may directly connect to our server.__

To run the Neurostack client from the command line, use `python neurostack.py`.

It takes three optional arguments:

> `--address`: ip: port to run Neurostack client on. The default is localhost:8002.\
>`--server_address`: ip: port for Neurostack server to connect to.\
>`--use_fake_data`: Use flag to generate fake data.

Example Usage:

>`python neurostack.py --server_address neurostack.neurotechuoft.com:8001 --address localhost:8002 --use_fake_data`


## Training and making predictions

To use, send a job to the backend with parameters and a callback function. To connect to the backend:

```python
from socketIO_client import SocketIO
import time
import json


def print_results(*args):
    print(args)

# server running on localhost:8002
socket_client = SocketIO('localhost', 8002)
socket_client.connect()

# initialize handlers
socket_client.on('uuid', print_results)
socket_client.on('train', print_results)
socket_client.on('predict', print_results)
```

To generate a UUID:

```python
# Generate a UUID
socket_client.emit('generate_uuid', None)
socket_client.wait(seconds=1)
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
socket_client.emit("p300_predict", args)
socket_client.wait(seconds=2)
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
socket_client.emit("p300_train", args)
socket_client.wait(seconds=2)
```

## WebSocket API

Below are Neurostack's API endpoints. Currently we support detection for the following:

- P300 brain wave
- Left/right brain activity

<br/>

#### generate_uuid
Generate a universally unique identifier.

Parameters:
> None

Returns:
> generated UUID

<br/>

#### start_streaming_raw_data

Start streaming raw EEG data. Applications that want to use this should listen for the event `raw_data`, which Neurostack will continuously emit to.

Parameters: 
>`uuid`: UUID of whoever is wants to stream raw data. This will open up a raw data stream for this specific user.

<br/>

#### stop_streaming_raw_data

Stop streaming raw EEG data. 

Parameters: 
>`uuid`: UUID of whoever is wants to stop streaming raw data.

<br/>

#### p300_predict
Make a prediction for whether P300 occurs at a timestamp.

Parameters:
> `uuid`: UUID of whoever is making a prediction. This will determine which classifier we will load up and use.  
>`timestamp`: timestamp of chunk of data

Emits an event called `predict` with arguments:
> `uuid`: UUID of caller  
> `timestamp`: timestamp of chunk of data
>`p300`: either True or False, predicting whether there is a P300 ERP  
>`score`: a value from 0 to 1 denoting the confidence in the prediction

<br/>

#### p300_train
Give a training example to the P300 classifier.

Parameters:
> `uuid`: UUID of whoever is making a prediction. This will determine which classifier we will load up and use.  
>`timestamp`: timestamp of chunk of data  
>`p300`: either True or False (or 1 or 0), depending on whether there should be a P300 ERP

Emits an event called `train` with arguments:
> `uuid`: UUID of caller 
> `timestamp`: timestamp of chunk of data 
> `acc`: accuracy of current classifier. This is either None/null (not enough training samples for training), or a number between 0 and 1.

<br/>

#### left_right_predict
Make a prediction for whether the user is using their left or right brain at a timestamp.

Parameters:
> `uuid`: UUID of whoever is making a prediction. This will determine which classifier we will load up and use.  
> `timestamp`: timestamp of chunk of data

Emits an event called `predict` with arguments:
> `uuid`: UUID of caller  
> `timestamp`: timestamp of chunk of data
> `left`: either True or False, predicting whether the user is using their left (True) or right (False) brain  
> `score`: a value from 0 to 1 denoting the confidence in the prediction

<br/>

#### left_right_train
Give a training example to the left/right brain classifier.

Parameters:
> `uuid`: UUID of whoever is making a prediction. This will determine which classifier we will load up and use.  
> `timestamp`: timestamp of chunk of data  
> `left`: True if using left brain, or False if using right brain

Emits an event called `train` with arguments:
> `uuid`: UUID of caller  
> `timestamp`: timestamp of chunk of data
> `acc`: accuracy of current classifier. This is either None/null (not enough training samples for training), or a number between 0 and 1.
