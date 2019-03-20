#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device loopback test in stream mode
#
# Author: Oleg Volkov olegv142@gmail.com

import sys
import random
sys.path.append('..')
from tbmc_dev import TBMCDev, TRIG, STATUS

opt_channels = None
rdy_timeout = 1.
cmd_len = 512

def parse_args():
	global opt_channels
	if '-c' in sys.argv:
		i = sys.argv.index('-c')
		opt_channels = int(sys.argv[i+1])
		del sys.argv[i:i+2]

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
	dev.configure_freq(1, 3, 3)
	dev.configure_rst(100, 100)
	dev.configure_tx(cmd_len, loop=True)
	dev.configure_rx(1, loopback=True)

	dev.trigger(TRIG.reset)
	dev.wait_ready(rdy_timeout)

	cmd = ''
	for i in range(cmd_len):
		cmd += chr(random.getrandbits(8))

	dev.cmd_put(cmd)

	j, total = 0, 0

	while True:
		it, off = 0, 0
		skip  = random.getrandbits(8)
		loops = random.getrandbits(8)

		if skip % 2: skip += 1

		dev.configure_rx(0, skip=skip, loopback=True)
		dev.trigger(TRIG.start)

		while True:
			if it >= loops:
				dev.trigger(TRIG.stop)
				dev.wait_status(0, STATUS.active, tout=rdy_timeout)
				break

			cmd_off = (off + skip) % cmd_len
			expect = cmd[cmd_off:cmd_len]
			while len(expect) < TBMCDev.rx_buff_chunk:
				expect += cmd
			expect = expect[0:TBMCDev.rx_buff_chunk]

			dev.wait_status(STATUS.data_rdy, tout=rdy_timeout)

			assert (dev.status() & STATUS.rd_unaligned) == 0

			r = dev.rx_buff_read_all(TBMCDev.rx_buff_chunk, channels)

			for c, resp in enumerate(r):
				if resp != expect:
					print >> sys.stderr, 'invalid response in channel %d on iteration %d:' % (c, it)
					print >> sys.stderr, 'cmd_len=%d, cmd[0]=%2x, skip=%d' % (cmd_len, ord(cmd[0]), skip)
					print >> sys.stderr, 'offset expect got'
					for i in range(TBMCDev.rx_buff_chunk):
						print >> sys.stderr, '%d\t%2x %2x' % (i, ord(expect[i]), ord(resp[i]))
					return -1

			total += TBMCDev.rx_buff_chunk * channels
			off += TBMCDev.rx_buff_chunk
			it  += 1

		print >> sys.stderr, '.',
		j += 1
		if j == 50:
			j = 0
			print >> sys.stderr, ' %d MBytes' % (total / 0x100000)

	return 0

if __name__ == '__main__':
	main()

 