from client.neurostack import Neurostack
from client.devices.muse import Muse

import argparse


# parse command line arguments
parser = argparse.ArgumentParser(description='Run Neurostack')

parser.add_argument('--address', type=str, default='localhost:8002',
                    help='ip:port to run Neurostack client on')
parser.add_argument('--server_address', type=str,
                    help='ip:port of Neurostack server to connect to')
parser.add_argument('--use_fake_data', action='store_true',
                    help='Use flag to generate fake data')

args = parser.parse_args()

# TODO: add something to specify which devices get passed in
muse = Muse()
muse.connect(fake_data=args.use_fake_data)
muse.start()

# create and run neurostack!
devices = [muse]
neurostack = Neurostack(devices=devices)

# connect to neurostack server
if args.server_address is not None:
    ip, port = args.server_address.split(':')
    neurostack.neurostack_connect(ip=ip, port=port)

# run neurostack client
neurostack.initialize_handlers()
host, port = args.address.split(':')
neurostack.run(host=host, port=port)
