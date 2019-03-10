#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device write performance test
#
# Author: Oleg Volkov olegv142@gmail.com

import time
import sys
sys.path.append('..')
from tbmc_dev import TBMCDev

blk_sz = 4096 * 8
blks = 1000
reg = 7

d = TBMCDev()
print d

blk = '\0' * blk_sz

started = time.time()

for _ in xrange(blks):
	d.write(reg, blk)

elapsed = time.time() - started

print blk_sz * blks / (1e6 * elapsed), 'MB/sec in 32 bit mode'

started = time.time()

for _ in xrange(blks):
	d.write16(reg, blk)

elapsed = time.time() - started

print blk_sz * blks / (1e6 * elapsed), 'MB/sec in 16 bit mode'
