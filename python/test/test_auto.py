#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device loopback test in auto mode
#
# Author: Oleg Volkov olegv142@gmail.com

import sys
import random
sys.path.append('..')
from tbmc_dev import TBMCDev, TRIG, STATUS

opt_channels = None
rdy_timeout = 1.

def parse_args():
	global opt_channels
	if '-c' in sys.argv:
		i = sys.argv.index('-c')
		opt_channels = int(sys.argv[i+1])
		del sys.argv[i:i+2]

def random_test(dev, chs):
	fast_mode = random.getrandbits(1)
	b16mode   = random.getrandbits(1)
	cmd_len   = 1 + random.getrandbits(9)
	rx_len    = 1 + random.getrandbits(11)
	wait      = random.getrandbits(1)
	auto_fr   = 1 + random.getrandbits(4)

	rx_len = max(rx_len, cmd_len)

	if b16mode:
		if cmd_len & 1: cmd_len += 1
		if rx_len  & 1: rx_len += 1

	cmd = ''
	for i in range(cmd_len):
		while True:
			v = random.getrandbits(8)
			# First byte should be non-zero
			if i or v:
				break
		cmd += chr(v)
		if not v and not i:
			wait = 0

	dev.configure_tx(cmd_len, tx_fast=fast_mode, b16=b16mode)
	dev.configure_rx(rx_len, wait=wait, loopback=True)

	dev.cmd_put(cmd)
	dev.trigger(TRIG.start)

	expect = cmd
	if len(expect) < rx_len:
		expect += '\0'*(rx_len-len(expect))

	assert len(expect) == rx_len

	dev.wait_status(STATUS.data_rdy | STATUS.completed, STATUS.active)

	if dev.status() & STATUS.ready:
		assert dev.find_not_ready()  is None
		assert dev.count_not_ready() == 0
	else:
		assert dev.find_not_ready()  == 0
		assert dev.count_not_ready() == chs

	assert (dev.status() & STATUS.rd_unaligned) == 0

	r = dev.rx_buff_read_all(rx_len, chs)

	for c, resp in enumerate(r):
		if resp != expect:
			print >> sys.stderr, 'invalid response in channel %d:' % c
			print >> sys.stderr, 'fast=%d, b16=%d, cmd_len=%d, rx_len=%d' % (fast_mode, b16mode, cmd_len, rx_len)
			print >> sys.stderr, 'offset expect got'
			for i in range(rx_len):
				print >> sys.stderr, '%d\t%2x %2x' % (i, ord(expect[i]), ord(resp[i]))
			return 0

	dev.trigger(TRIG.auto)

	for fr in range(auto_fr):
		r = dev.rx_buff_read_all_on_ready(rx_len, chs, tout=rdy_timeout)
		err = False
		for c, resp in enumerate(r):
			if resp != expect:
				print >> sys.stderr, 'invalid response in channel %d on frame %d:' % (c, fr)
				print >> sys.stderr, 'fast=%d, b16=%d, cmd_len=%d, rx_len=%d' % (fast_mode, b16mode, cmd_len, rx_len)
				print >> sys.stderr, 'offset expect got'
				for i in range(rx_len):
					print >> sys.stderr, '%d\t%2x %2x' % (i, ord(expect[i]), ord(resp[i]))
				err = True
		if err:
			return 0

	return rx_len * chs * (auto_fr + 1)

def main():
	dev = TBMCDev()

	parse_args()
	if opt_channels is not None:
		channels = opt_channels
		assert channels <= dev.total_channels()
	else:
		channels = dev.total_channels()

	print '%s, testing %d channels' % (dev, channels)

	dev.configure_chans(channels)
	# Use the fastest rate - 25MHz
	dev.configure_freq(0, 3, 3)
	dev.configure_rst(100, 100)
	dev.configure_rx(1, loopback=True)

	i, j, total = 0, 0, 0
	while True:
		dev.trigger(TRIG.reset)
		dev.wait_ready(rdy_timeout)
		r = random_test(dev, channels)
		if not r:
			return -1
		total += r
		i += 1
		if not (i % 10):
			print >> sys.stderr, '.',
			j += 1
			if j == 50:
				j = 0
				print >> sys.stderr, ' %d MBytes' % (total / 0x100000)

	return 0

if __name__ == '__main__':
	main()

 
