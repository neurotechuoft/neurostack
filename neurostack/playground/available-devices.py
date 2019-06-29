# pip install pyusb
import usb

devices = usb.core.find(find_all=True, idVendor=0x0403, idProduct=0x6015)
for device in devices:
    print(device)
    # print(device.idVendor == 0x0403)
    # print(device.idProduct == 0x6015)
    # print(device.manufacturer == "FTDI")
    # print(device.product == "FT231X USB UART")
