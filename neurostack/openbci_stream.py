# import neurostack.devices as devices
import devices


#
#
# # def main():
# #     openbci_ids = devices.OpenBCI.available_devices()
# #
# #     if openbci_ids is None:
# #         return
# #
# #     neurostack = Neurostack(
# #         devices=[
# #             devices.OpenBCI(openbci_ids[0]),
# #         ],
# #         tags=[
# #             ui_tag,
# #         ],
# #         subscribers=[
# #             mmc_socket_connection,
# #             p300_socket_connection,
# #         ]
# #     )
# #
# #     neurostack.start()
#
#     # main()
#


def main():
    openbci = devices.OpenBCI(device_id='COM3')
    openbci.connect()
    print("Connected!")
    print(openbci.openbci_cyton.port)
    openbci.start()
    print("Hi")
    # print(devices.OpenBCI.available_devices())
    print("Hello")


#


main()
