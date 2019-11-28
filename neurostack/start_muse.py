from devices.muse import Muse
from devices.openbci import OpenBCI
# muse = Muse()
# muse.connect(fake_data=True)
# muse.start()
def print_stream(sample):
    print (sample.channels_data)
openbci = OpenBCI()
openbci.connect()
openbci.start(print_stream)





# connect neurostack server
# muse.neurostack_connect('35.222.93.233', 8001)
# muse.neurostack_connect('localhost', 8001)

# run client as server as well (to allow API for front end)
# muse.initialize_handlers()
# muse.app.run(host='localhost', port=8002)
