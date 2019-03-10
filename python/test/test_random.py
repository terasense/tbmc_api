#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device loopback test with random settings
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
	loop      = random.getrandbits(1)
	cmd_len   = 1 + random.getrandbits(9)
	rx_len    = 1 + random.getrandbits(11)
	skip      = random.getrandbits(10)
	wait      = random.getrandbits(1)

	if b16mode:
		if cmd_len & 1: cmd_len += 1
		if rx_len  & 1: rx_len += 1
		if skip    & 1: skip += 1

	cmd = ''
	for i in range(cmd_len):
		v = random.getrandbits(8)
		cmd += chr(v)
		if not v and not i:
			wait = 0

	dev.configure_tx(cmd_len, tx_fast=fast_mode, b16=b16mode, loop=loop)
	dev.configure_rx(rx_len, skip=skip, wait=wait, loopback=True)

	dev.cmd_put(cmd)
	dev.trigger(TRIG.start)

	if not loop:
		if skip >= cmd_len:
			expect = '\0'*rx_len
		else:
			expect = cmd[skip:cmd_len]
			if len(expect) >= rx_len:
				expect = expect[0:rx_len]
			else:
				expect += '\0'*(rx_len-len(expect))
	else:
		skip = skip % cmd_len
		expect = cmd[skip:cmd_len]
		while len(expect) < rx_len:
			expect += cmd
		expect = expect[0:rx_len]

	assert len(expect) == rx_len

	dev.wait_status(STATUS.data_rdy | STATUS.completed, STATUS.active)

	if dev.status() & STATUS.ready:
		assert dev.find_not_ready() is None
		assert dev.count_not_ready() == 0
	else:
		assert dev.find_not_ready()  == 0
		assert dev.count_not_ready() == chs

	assert (dev.status() & STATUS.rd_unaligned) == 0

	r = dev.rx_buff_read_all(rx_len, chs)

	for c, resp in enumerate(r):
		if resp != expect:
			print >> sys.stderr, 'invalid response in channel %d:' % c
			print >> sys.stderr, 'fast=%d, b16=%d, loop=%d, cmd_len=%d, rx_len=%d, skip=%d' % (fast_mode, b16mode, loop, cmd_len, rx_len, skip)
			print >> sys.stderr, 'offset expect got'
			for i in range(rx_len):
				print >> sys.stderr, '%d\t%2x %2x' % (i, ord(expect[i]), ord(resp[i]))
			return 0

	return rx_len * chs

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

	dev.trigger(TRIG.reset)
	dev.wait_ready(rdy_timeout)

	i, j, total = 0, 0, 0
	while True:
		r = random_test(dev, channels)
		if not r:
			return -1
		total += r
		i += 1
		if not (i % 100):
			print >> sys.stderr, '.',
			j += 1
			if j == 50:
				j = 0
				print >> sys.stderr, ' %d MBytes' % (total / 0x100000)

	return 0

if __name__ == '__main__':
	main()

