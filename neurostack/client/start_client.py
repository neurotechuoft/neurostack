from client.neurostack import Neurostack
from client.devices.muse import Muse
from client.devices.openbci import OpenBCI

import argparse


# parse command line arguments
parser = argparse.ArgumentParser(description='Run Neurostack')

parser.add_argument('--devices', nargs='+',
                    choices=['muse', 'openbci'],
                    help='Names of devices to add. Can choose from "muse" or "openbci", and can select multiple devices.')
parser.add_argument('--address', type=str, default='localhost:8002',
                    help='ip:port to run Neurostack client on')
parser.add_argument('--server_address', type=str,
                    help='ip:port of Neurostack server to connect to')
parser.add_argument('--use_fake_data', nargs='+',
                    help='Give a "true", "false", or "none" per device for whether it should stream fake data or not.')

args = parser.parse_args()


# convert use_fake_data argument to True, False, or None
use_fake_data = []
for arg in args.use_fake_data:
    if arg.lower() in ('yes', 'true', 't', 'y', '1'):
        use_fake_data.append(True)
    elif arg.lower() in ('no', 'false', 'f', 'n', '0'):
        use_fake_data.append(False)
    else:
        use_fake_data.append(None)

# decide which devices Neurostack is using
devices = []
for device in args.devices:
    if device == 'muse':
        devices.append(Muse())
    elif device == 'openbci':
        devices.append(OpenBCI())

# create and run neurostack!
neurostack = Neurostack(devices=devices)
neurostack.connect_devices(use_fake_data_list=use_fake_data)
neurostack.start_devices()

# connect to neurostack server
if args.server_address is not None:
    ip, port = args.server_address.split(':')
    neurostack.neurostack_connect(ip=ip, port=port)

# run neurostack client
neurostack.initialize_handlers()
host, port = args.address.split(':')
neurostack.run(host=host, port=port)
