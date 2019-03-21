# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: T-BUS controller
#
# Author: Oleg Volkov olegv142@gmail.com

import struct
import random
import log
import tbus_defs as tb
import tmod_defs as tm
from tbmc_dev import TBMCDev, TRIG, STATUS

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

	def bus_srq(self):
		"""Issue SRQ on the bus"""
		log.dbg('  BUS srq')
		self.dev.trigger(TRIG.srq)
		self.dev.wait_ready(TBUSCtl.bus_timeout)

	def bus_init(self):
		"""Initialize controller"""
		log.dbg('%s', self.dev)
		if self.dev.channels < self.cfg.nchannels:
			raise RuntimeError('controller supports %d channels, %d channels required' % (self.dev.channels, self.cfg.nchannels))

		log.dbg('initializing')
		div = int(TBMCDev.master_clk / self.cfg.tbus_freq)
		if float(TBMCDev.master_clk) / div != self.cfg.tbus_freq:
			raise RuntimeError("can't set bus frequency " + str(self.cfg.tbus_freq))

		self.cfg.f_div = div

		poll_cmd = self._mk_cmd(tb.cmd_poll, addr=tm.status_addr, data='\x00\xff')
		self.dev.configure_chans(self.cfg.nchannels)
		self.dev.configure_freq(div, self.cfg.tbus_tx_idle, self.cfg.tbus_turbo_idle)
		self.dev.configure_rst(TBUSCtl.rst_time, TBUSCtl.clk_hold_time)
		self.dev.configure_tx(len(poll_cmd))
		self.dev.configure_rx(len(poll_cmd) + 2, wait = True)
		self.bus_reset()

		log.dbg('probing modules')
		self.dev.cmd_put(poll_cmd)
		self.dev.trigger(TRIG.start)
		self.dev.wait_status(
				STATUS.ready | STATUS.tx_done | STATUS.data_rdy | STATUS.completed, STATUS.active,
				tout=TBUSCtl.bus_timeout
			)
		r = self.dev.rx_buff_read_all(len(poll_cmd) + 2, self.cfg.nchannels)
		assert len(r) == self.cfg.nchannels
		chain, mod_version = None, None
		for i, d in enumerate(r):
			rcnt = self._check_resp(poll_cmd, d, i)
			va, vb = struct.unpack('BB', d[tb.hdr_sz:tb.hdr_sz+2])
			if va != vb:
				raise RuntimeError('mixed module versions in channel #%d' % i)
			log.dbg('    #%d: %d modules v.%x', i, rcnt, va)
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
		assert (data_len == 0) == ((cmd_code & tb.cmd_has_data_) == 0)
		len1 = data_len - 1 if (cmd_code & tb.cmd_has_data_) else 0
		assert 0 <= len1 and len1 < tb.max_data_length
		log.dbg('  BUS %-5s @%x %d bytes', tb.cmd_names[cmd_code], addr, data_len)
		hdr = struct.pack(tb.hdr_fmt, cmd_code, len1, addr,
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
		req_  = struct.unpack(tb.hdr_fmt, req[:tb.hdr_sz])
		resp_ = struct.unpack(tb.hdr_fmt, resp[:tb.hdr_sz])
		if req_[:4] != resp_[:4]:
			raise RuntimeError('T-BUS %s returned unexpected header in channel %d: sent %s, received %s' % (
					tb.cmd_names[req_[0]], chan, repr(req_), repr(resp_)
				))
		if resp_[4]:
			raise RuntimeError('T-BUS %s returned status %d in channel %d (%d responses)' % (
					tb.cmd_names[req_[0]], resp_[4], chan, resp_[5]
				))
		return resp_[5]

	@staticmethod
	def _check_resp_data(req, resp, chan):
		"""Compare data received with data sent."""
		req_data, resp_data = req[tb.hdr_sz:], resp[tb.hdr_sz:len(req)]
		if req_data != resp_data:
			info, nerrs = 'no difference', 0
			req_ = struct.unpack(tb.hdr_fmt, req[:tb.hdr_sz])
			for i, req_b in enumerate(req_data):
				if resp_data[i] != req_b:
					if not nerrs:
						info = '[%d] sent=0x%02x, recv=0x%02x' % (i, ord(req_b), ord(resp_data[i]))
					nerrs += 1
			info += ' (%d invalid bytes)' % nerrs
			raise RuntimeError('T-BUS %s + %d bytes returned unexpected data in channel %d: %s' % (
					tb.cmd_names[req_[0]], len(req), chan, info
				))

	@staticmethod
	def _check_resp_idle(resp, req_len, chan):
		"""Check trailing bytes of the response."""
		for i in range(req_len, len(resp)):
			if ord(resp[i]) != 0:
				resp_ = struct.unpack(tb.hdr_fmt, resp[:tb.hdr_sz])
				raise RuntimeError('T-BUS %s returned unexpected idle byte 0x%x in channel %d' % (
						tb.cmd_names[resp_[0]], ord(resp[i]), chan
					))

	@staticmethod
	def round_size(sz):
		return sz + (sz & 1) + 2  # make it even and pad with zero bytes

	def _send_cmd(self, cmd_code, addr, data, check_data):
		"""Send command and returns the array of responses"""
		wait = (cmd_code==tb.cmd_wait)
		cmd = self._mk_cmd(cmd_code, addr, data)
		rx_len = TBUSCtl.round_size(len(cmd))
		tx_idle = (self.cfg.tbus_tx_idle, self.cfg.tbus_wt_idle)[wait]

		self.dev.configure_freq(self.cfg.f_div, tx_idle, self.cfg.tbus_turbo_idle)
		self.dev.configure_tx(len(cmd), tx_fast = False, b16 = True)
		self.dev.configure_rx(rx_len, skip = 4 * self.chain, wait = wait)

		self.dev.cmd_put(cmd)
		self.dev.trigger(TRIG.start)
		self.dev.wait_status(
				STATUS.ready | STATUS.tx_done | STATUS.data_rdy | STATUS.completed, STATUS.active,
				tout=TBUSCtl.bus_timeout
			)
		r = self.dev.rx_buff_read_all(rx_len, self.cfg.nchannels)
		assert len(r) == self.cfg.nchannels
		for i, d in enumerate(r):
			rcnt = self._check_resp(cmd, d, i, check_data)
			if rcnt != self.chain:
				raise RuntimeError('unexpected number of responses in channel %d: expected %d, received %d' % (i, self.chain, rcnt))
		return r

	def bus_cmd(self, cmd_code, addr = 0, data = None):
		"""
		Send single response command. Raise exception if the command status is not success
		or the data received differs from the data sent.
		"""
		assert (cmd_code & tb.cmd_mult_response_) == 0
		assert cmd_code != tb.cmd_poll
		self._send_cmd(cmd_code, addr, data, data is not None)

	def bus_write(self, addr, data):
		"""Write data to the specified address"""
		self.bus_cmd(tb.cmd_write, addr, data)

	def bus_wait(self):
		"""Issue wait command"""
		self.bus_cmd(tb.cmd_wait)

	def bus_read_raw(self, addr, data_len):
		"""
		Send read command. Raise exception if the command status is not success.
		Returns the array of (number of responses, data) tuples.
		"""
		assert data_len > 0
		assert (data_len & 1) == 0

		resp_sz = data_len * self.chain
		chan_total = tb.hdr_sz + resp_sz
		r, chan_total_ = [None] * self.cfg.nchannels, TBUSCtl.round_size(chan_total)
		stream_mode = chan_total_ > TBMCDev.max_rx_length

		log.dbg('%s %d bytes', 'streaming' if stream_mode else 'reading', data_len)

		cmd = self._mk_cmd(tb.cmd_read, addr, None, data_len)
		assert len(cmd) == tb.hdr_sz

		self.dev.configure_freq(self.cfg.f_div, self.cfg.tbus_tx_idle, self.cfg.tbus_turbo_idle)
		self.dev.configure_tx(len(cmd), tx_fast = True, b16 = True)
		self.dev.configure_rx(0 if stream_mode else chan_total_, skip = 4 * self.chain)

		self.dev.cmd_put(cmd)
		self.dev.trigger(TRIG.start)

		while chan_total_ > 0:
			self.dev.wait_status(STATUS.data_rdy, 0, tout=TBUSCtl.bus_timeout)
			chunk_data = self.dev.rx_buff_read_all(TBMCDev.rx_buff_chunk if stream_mode else chan_total_, self.cfg.nchannels)
			assert len(chunk_data) == self.cfg.nchannels
			for i, resp in enumerate(chunk_data):
				if r[i] is None: r[i] = []
				r[i].append(resp[:chan_total_])
			chan_total_ -= len(resp)

		if stream_mode:
			self.dev.trigger(TRIG.stop)
			self.dev.wait_status(STATUS.ready, STATUS.active, tout=TBUSCtl.bus_timeout)

		chan_data = [''.join(chunks) for chunks in r]
		for i, data in enumerate(chan_data):
			rcnt = self._check_resp_hdr(cmd, data, i)
			if rcnt != self.chain:
				raise RuntimeError('unexpected number of responses in channel %d: expected %d, received %d' % (i, self.chain, rcnt))
			self._check_resp_idle(data, chan_total, i)

		return (self.modules, ''.join([data[tb.hdr_sz:chan_total] for data in chan_data]))

	def bus_read_coherent(self, addr, data_len):
		"""
		Read coherent data from the specified address. Raise exception if the command status
		is not success or the data is not coherent. Returns (r_cnt, data) tuple.
		"""
		data, buff = '\x00\xff' * data_len, None
		r = self._send_cmd(tb.cmd_poll, addr, data, False)
		for i, d in enumerate(r):
			resp = d[tb.hdr_sz:tb.hdr_sz+len(data)]
			r_or, r_and = resp[::2], resp[1::2]
			if buff is None: buff = r_or
			if r_or != r_and or r_or != buff:
				raise RuntimeError('data is not coherent in channel %d' % i)

		return (self.modules, buff)

	def bus_read(self, addr, data_len):
		"""Read data from the specified address. Returns the array of the data responses."""
		r = self.bus_read_raw(addr, data_len)
		return [r[1][i*data_len:(i+1)*data_len] for i in range(r[0])]

	def bus_read_struct(self, addr, fmt):
		"""
		Read data from the specified address and parse it according to specified format.
		Returns the array of the data tuples.
		"""
		r = self.bus_read(addr, struct.calcsize(fmt))
		return [struct.unpack(fmt, d) for d in r]

	def bus_read_struct_coherent(self, addr, fmt):
		"""
		Read coherent data from the specified address and parse it according to specified format
		Returns (r_cnt, data_tuple) tuple.
		"""
		r = self.bus_read_coherent(addr, struct.calcsize(fmt))
		return (r[0], struct.unpack(fmt, r[1]))


if __name__ == '__main__':
	import sys
	from config import tbus_conf as conf
	if '-v' in sys.argv:
		log.level = log.l_trc
	dev = TBMCDev()
	ctl = TBUSCtl(dev, conf)
	ctl.bus_init()
	print ctl

	
