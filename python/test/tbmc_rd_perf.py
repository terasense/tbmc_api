#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device read performance test
#
# Author: Oleg Volkov olegv142@gmail.com

import time
import sys
sys.path.append('..')
from tbmc_dev import TBMCDev

blk_sz = 4096 * 8
blks = 1000
reg = 6

d = TBMCDev()
print d

started = time.time()

for _ in xrange(blks):
	d.read(reg, blk_sz)

elapsed = time.time() - started

print blk_sz * blks / (1e6 * elapsed), 'MB/sec'
