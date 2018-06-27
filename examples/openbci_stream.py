import neurostack.devices as devices
from neurostack import Neurostack

if __name__ == "main":
    openbcis = devices.OpenBCI.available_devices()

    neurostack = Neurostack(
        device=devices.OpenBCI(),
        subscribers=[
            mmc_socket_connection,
            p300_socket_connection,
        ],
        tags=[
            ui_tag,
        ]
    )

    neurostack.start()
