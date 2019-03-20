# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: TS32 applets communication utilities
#
# Author: Oleg Volkov olegv142@gmail.com

import sys, os
import numpy as np
import struct
import tmod_defs as tmod
import msp430txt as ldr
from tmod_hlp import *
import log

data_channels = 35
data_len = data_channels * 2
max_data_value = 1024

def configure(ctl, conf):
	"""Reset modules, load applet if necessary and configure timeout"""
	path = os.path.join(os.path.dirname(conf.__file__), conf.code_path)
	log.dbg('using code path %s', path)
	segs = ldr.load_file(path)
	if segs is None:
		raise RuntimeError("failed to load %s", path)
	if len(segs) != 1:
		raise RuntimeError("can't load %d segments from %s" % (len(segs), path))

	addr, code = segs[0]
	conf._start_address = addr
	chksum = tmod.get_chksum(code)
	log.dbg('applet is loaded: @%x %d bytes, chksum=%08x', addr, len(code), chksum)

	log.notice('resetting the bus')
	reset(ctl)

	log.notice('queering modules status')
	try:
		r = read_status(ctl)
	except RuntimeError:
		notice('erasing flash')
		srq_sync(ctl, tmod.srq_flash_ers)
		r = read_status(ctl)

	if not (r[1][2] & tmod.chksum_valid):
		raise RuntimeError('no check sum reported')

	if r[1][4] != chksum:
		log.inf('loading applet to flash')
		program(ctl, addr, code)
	else:
		log.notice('applet is already loaded to flash')

def acquire_raw(ctl, conf):
	"""Execute applet and returns (number of module responses, raw data string) tuple"""
	log.notice('starting applet ..')
	srq_sync(ctl, tmod.srq_proc, 0, conf._start_address, struct.pack(
			'HBB',
			conf.int_time,
			conf.timer_frame | (conf.reset_time << 3) | (conf.timer_clk_div << 6),
			conf.adc_sh_time | (conf.adc_clk_div << 2 ) | (conf.no_cdc << 5) | (conf.temp_test << 6) | (conf.vcc_ref << 7)
		), conf.read_delay)
	log.notice("reading results ..")
	r = ctl.bus_read_raw(tmod.srq_buff_addr + 4, data_len)
	return r

def array_from_raw(data):
	"""Create numpy array from raw data"""
	a = np.fromstring(data[1], dtype=np.int16)
	assert a.size == data_channels * data[0]
	if np.any(a >= max_data_value):
		raise RuntimeError('the data is out of valid range')
	return np.reshape(a, (a.size/data_channels, data_channels))

def acquire(ctl, conf):
	"""Execute applet and returns results as numpy array"""
	data = acquire_raw(ctl, conf)
	return array_from_raw(data)

if __name__ == '__main__':
	import tbmc_dev
	import tbus_ctl
	import config.tbus_conf as tbus_conf
	import config.ts32_conf as applet_conf
	if '-v' in sys.argv:
		# verbose
		log.level = log.l_trc
	if '-l' in sys.argv:
		# long output
		np.set_printoptions(threshold='nan')

	dev = tbmc_dev.TBMCDev()
	ctl = tbus_ctl.TBUSCtl(dev, tbus_conf)
	ctl.bus_init()

	configure(ctl, applet_conf)
	print acquire(ctl, applet_conf)
