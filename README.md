# Neurostack

**(In development)**

Streaming brain waves to machine learning services, made easy.

```python
from neurostack import Neurostack
import neurostack.devices as devices

if __name__ == "main":

    neurostack = Neurostack(
        device = devices.OpenBCI,
        subscribers = [
            mmc_socket_connection,
            p300_socket_connection,
        ],
        tags = [
            ui_tag,
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

Stop streaming EEG data from device, and stop publishing data to subscribers. Connection to device remains intact, and device is not turn off.

***shutdown()***

Close connection to device, WebSocket connections to publishers, and tag sources.
