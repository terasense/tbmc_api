#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: Memory copy throughput test
#
# Author: Oleg Volkov olegv142@gmail.com

import time

Mb = 1024*1024
copy_bytes = 4*Mb
loops = 100

buff = 'x' * copy_bytes
buff = bytearray(buff)
start = time.time()

for _ in range(loops):
	buff = buff[:]
	
elapsed = time.time() - start
print copy_bytes * loops / (elapsed * Mb), 'MB/sec'
