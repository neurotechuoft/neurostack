import neurostack.devices as devices
from neurostack import Neurostack


def main():
    openbci_ids = devices.OpenBCI.available_devices()

    if openbci_ids is None:
        return

    neurostack = Neurostack(
        devices=[
            devices.OpenBCI(openbci_ids[0]),
        ],
        subscribers=[
            mmc_socket_connection,
            p300_socket_connection,
        ],
        tags=[
            ui_tag,
        ]
    )

    neurostack.start()


if __name__ == "main":
    main()
