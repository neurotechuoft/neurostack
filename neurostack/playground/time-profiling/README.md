We want to compare the time it takes to get a signal from the OpenBCI board
using the NodeJS and Python implementations. I have included the code that I
used to do so.

NodeJS average sample time: 0.4ms
Python average sample time: 4.8ms

(Note: the Python part is 0.021ms, however it is without the serialport reads --
I need to test with the board first to get an accurate result)

(Python tested on VM, so result much slower)
