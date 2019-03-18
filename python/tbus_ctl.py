# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: T-BUS controller
#
# Author: Oleg Volkov olegv142@gmail.com

import struct
import random
import log
import tbus_defs as tbus
import tmod_defs as tmod
from tbmc_dev import *

class TBUSCtl:
	# Hard-coded parameters
	rst_time      = 100
	clk_hold_time = 100
	bus_timeout   = 1.

	def __init__(self, dev, cfg):
		"""
		Create controller instance given the TBMCDev instance and the configuration object
		"""
		self.dev = dev
		self.cfg = cfg
		self.chain = None
		self.modules = None
		self.mod_version = None

	def bus_reset(self):
		"""Issue hard reset on the bus"""
		log.dbg('  BUS reset')
		self.dev.trigger(TRIG.reset)
		self.dev.wait_ready(TBUSCtl.bus_timeout)

	def bus_init(self, force_load = False):
		"""Initialize controller"""
		log.notice('%s' % self.dev)
		if self.dev.channels < self.cfg.nchannels:
			raise RuntimeError('controller supports %d channels, %d channels required' % (self.dev.channels, self.cfg.nchannels))

		log.dbg('initializing')
		div = int(TBMCDev.master_clk / self.cfg.tbus_freq)
		if float(TBMCDev.master_clk) / div != self.cfg.tbus_freq:
			raise RuntimeError("can't set bus frequency " + str(self.cfg.tbus_freq))

		self.cfg.f_div = div

		poll_cmd = self._mk_cmd(tbus.cmd_poll, addr=tmod.status_addr, data='\x00\xff')
		self.dev.configure_chans(self.cfg.nchannels)
		self.dev.configure_freq(div, self.cfg.tbus_tx_idle, self.cfg.tbus_turbo_idle)
		self.dev.configure_rst(TBUSCtl.rst_time, TBUSCtl.clk_hold_time)
		self.dev.configure_tx(len(poll_cmd))
		self.dev.configure_rx(len(poll_cmd) + 2, wait = True)
		self.bus_reset()

		log.dbg('probing modules')
		self.dev.cmd_put(poll_cmd)
		self.dev.trigger(TRIG.start)
		self.dev.wait_status(STATUS.ready | STATUS.tx_done | STATUS.data_rdy | STATUS.completed, STATUS.active, tout=TBUSCtl.bus_timeout)
		r = self.dev.rx_buff_read_all(len(poll_cmd) + 2, self.cfg.nchannels)
		assert len(r) == self.cfg.nchannels
		chain, mod_version = None, None
		for i, d in enumerate(r):
			rcnt = self._check_resp(poll_cmd, d, i)
			va, vb = struct.unpack('BB', d[tbus.hdr_sz:tbus.hdr_sz+2])
			if va != vb:
				raise RuntimeError('mixed module versions in channel #%d' % i)
			log.dbg('    #%d: %d modules v.%x' % (i, rcnt, va))
			if chain is None:
				chain, mod_version = rcnt, va
			else:
				if chain != rcnt:
					raise RuntimeError('unequal number of modules in T-BUS channels')
				if mod_version != va:
					raise RuntimeError('mixed module versions in T-BUS channels')

		if not chain:
			raise RuntimeError('no modules detected')
		if mod_version < 0x12:
			raise RuntimeError('obsolete modules version %x' % mod_version)

		# We are not expecting the number of modules to be changed after initialization
		self.chain = chain
		self.modules = chain * self.cfg.nchannels
		self.mod_version = mod_version

	def __str__(self):
		if self.chain is None:
			return '%s uninitialized' % self.dev
		return '%s %dx%d modules v.%x' % (self.dev, self.cfg.nchannels, self.chain, self.mod_version)

	def _mk_cmd(self, cmd_code, addr = 0, data = None, data_len = None):
		"""Create and return T-BUS command"""
		if data_len is None:
			data_len = len(data) if data is not None else 0
		assert (data_len == 0) == ((cmd_code & tbus.cmd_has_data_) == 0)
		len1 = data_len - 1 if (cmd_code & tbus.cmd_has_data_) else 0
		assert 0 <= len1 and len1 < tbus.max_data_length
		log.dbg('  BUS %-5s @%x %d bytes' % (tbus.cmd_names[cmd_code], addr, data_len))
		hdr = struct.pack(tbus.hdr_fmt, cmd_code, len1, addr,
			0 if self.cfg.skip_cmd_cookies else int(random.getrandbits(8)), 0, 0)
		if data is None:
			return hdr
		else:
			return hdr + data

	@staticmethod
	def _check_resp(req, resp, chan, check_data = False):
		"""Check command response. Returns the number of responses."""
		# We expect response to have trailing idle bytes
		assert len(resp) > len(req)
		rcnt = TBUSCtl._check_resp_hdr(req, resp, chan)
		if (check_data): TBUSCtl._check_resp_data(req, resp, chan)
		TBUSCtl._check_resp_idle(resp, len(req), chan)
		return rcnt

	@staticmethod
	def _check_resp_hdr(req, resp, chan):
		"""Check response header. Returns the number of responses."""
		req_  = struct.unpack(tbus.hdr_fmt, req[:tbus.hdr_sz])
		resp_ = struct.unpack(tbus.hdr_fmt, resp[:tbus.hdr_sz])
		if req_[:4] != resp_[:4]:
			raise RuntimeError('T-BUS %s returned unexpected header in channel %d: sent %s, received %s' % (
					tbus.cmd_names[req_[0]], chan, repr(req_), repr(resp_)
				))
		if resp_[4]:
			raise RuntimeError('T-BUS %s returned status %d in channel %d (%d responses)' % (
					tbus.cmd_names[req_[0]], resp_[4], chan, resp_[5]
				))
		return resp_[5]

	@staticmethod
	def _check_resp_data(req, resp, chan):
		"""Compare data received with data sent."""
		req_data, resp_data = req[tbus.hdr_sz:], resp[tbus.hdr_sz:len(req)]
		if req_data != resp_data:
			info, nerrs = 'no difference', 0
			req_ = struct.unpack(tbus.hdr_fmt, req[:tbus.hdr_sz])
			for i, req_b in enumerate(req_data):
				if resp_data[i] != req_b:
					if not nerrs:
						info = '[%d] sent=0x%02x, recv=0x%02x' % (i, ord(req_b), ord(resp_data[i]))
					nerrs += 1
			info += ' (%d invalid bytes)' % nerrs
			raise RuntimeError('T-BUS %s + %d bytes returned unexpected data in channel %d: %s' % (
					tbus.cmd_names[req_[0]], len(req), chan, info
				))

	@staticmethod
	def _check_resp_idle(resp, req_len, chan):
		"""Check trailing bytes of the response."""
		for i in range(req_len, len(resp)):
			if ord(resp[i]) != 0:
				resp_ = struct.unpack(tbus.hdr_fmt, resp[:tbus.hdr_sz])
				raise RuntimeError('T-BUS %s returned unexpected idle byte 0x%x in channel %d' % (
						tbus.cmd_names[resp_[0]], ord(resp[i]), chan
					))


if __name__ == '__main__':
	from config import tbus_conf as conf
	dev = TBMCDev()
	ctl = TBUSCtl(dev, conf)
	ctl.bus_init()
	print ctl

	
	
