#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device loopback mode test
#
# Author: Oleg Volkov olegv142@gmail.com

import sys
sys.path.append('..')
from tbmc_dev import TBMCDev, TRIG, STATUS

opt_channels = None
rdy_timeout = 1.
cmd_length = 512
loops = 1000

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
	dev.configure_freq(0, 3, 3)
	dev.configure_rst(100, 100)
	dev.configure_tx(cmd_length, tx_fast=False, b16=True)
	dev.configure_rx(cmd_length, wait=True, loopback=True)

	data = ''
	for i in range(cmd_length):
		data += chr((i+13)%255)

	dev.trigger(TRIG.reset)
	dev.wait_ready(rdy_timeout)

	dev.trigger(TRIG.srq)
	dev.wait_ready(rdy_timeout)

	dev.cmd_put(data)

	for i in range(loops):
		print >> sys.stderr, '.',
		dev.trigger(TRIG.start)
		dev.wait_status(STATUS.data_rdy | STATUS.completed, STATUS.active, rdy_timeout)
		res = dev.rx_buff_read_all(cmd_length, channels)
		for i, buff in enumerate(res): 
			if buff != data:
				print >> sys.stderr, '\nerror in channel %d' % i
				for ch in buff:
					print '%x' % ord(ch)
				return -1

	print '\ndone'
	return 0

if __name__ == '__main__':
	sys.exit(main())

 