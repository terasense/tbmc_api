# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device communication helper
#
# Author: Oleg Volkov olegv142@gmail.com

from mmdev import MmDev
import time

class TRIG:
	# Trigger bits (index)
	reset = 0  # Initiate bus reset cycle
	srq   = 1  # Initiate bus srq   cycle 
	start = 2  # Start command transmission
	stop  = 8  # Stop command transmission is stream mode
	auto  = 12 # Start auto mode

class STATUS:
	# Status bits
	ready        = 1 << 0  # LED1  The bus data input inverted, modules drive it low after successful startup
	reset        = 1 << 1  #       Set to 1 if bus srq line is driven low
	hold         = 1 << 2  #       Set to 1 if bus clock line is driven low indicating hard bus reset
	active       = 1 << 3  # LED2  Set to 1 if the transmission is in progress
	tx_done      = 1 << 4  # LED3  Set to 1 if the command transmission is completed and we are feeding zeroes to the bus
	stopping     = 1 << 6  # LED4  Set to 1 if transmitter is stopping (completing last byte transmission)
	error        = 1 << 7  # LED8  Set to 1 if transmitter error is detected (due to invalid configuration in particular)
	data_rdy     = 1 << 8  #       Set to 1 if the response data is ready to be read from receiver buffer
	completed    = 1 << 9  # LED6  Set to 1 if the all requested response data were received and transmitter is stopped
	pause        = 1 << 10 # LED5  Set to 1 if the transmitter is paused waiting the buffer to be freed
	rd_unaligned = 1 << 11 #       Set to 1 if read address is not aligned to the chunk boundary
	underrun     = 1 << 15 # LED7  Set to 1 if the client read from receiver buffer more than amount of data available (streaming mode only)
	# Bits indicating fatal error
	failure   = error | underrun

class TBMCDev(MmDev):
	"""TBUS controller core implementation"""
	name = 'axi_tbmc'
	magic = 0x4f56

	# controller registers
	# writeable
	wr_triggers    = 0
	wr_cfg_ctl     = 1
	wr_freq_ctl    = 2
	wr_rst_ctl     = 3
	wr_cmd_ctl     = 4
	wr_rx_ctl      = 5
	wr_cmd_buff    = 6
	# readable
	rd_version     = 0
	rd_status      = 1
	rd_input_state = 2
	rd_rx_buff     = 6

	# other constants:
	# the command buffer size
	max_cmd_length = 512
	# the single channel rx buffer size
	max_rx_length  = 2048

	def __init__(self):
		"""Create device instance"""
		MmDev.__init__(self, TBMCDev.name)
		self.read_version()

	def read_version(self):
		"""Read controller version information"""
		v = self.peek(TBMCDev.rd_version)
		assert v >> 16 == TBMCDev.magic
		self.channels = 1 + (v & ((1 << 10) - 1))
		self.version = (v & ((1 << 16) - 1)) >> 10

	def total_channels(self):
		return self.channels

	def __str__(self):
		"""Returns controller's readable name"""
		return '%s v.%d %d channels' % (
				TBMCDev.name, self.version, self.channels
			)

	def status(self):
		"""Read controller status"""
		return self.peek(TBMCDev.rd_status) & 0xffff

	def wait_status(self, set_bits, clr_bits = 0, tout = None):
		"""Wait the particular status bits to be set or cleared"""
		if tout:
			deadline = time.time() + tout
		while True:
			st = self.status()
			if (st & set_bits) == set_bits and (st & clr_bits) == 0:
				break
			if (st & STATUS.failure):
				raise RuntimeError('%s has failure status %#x' % (self, st))
			if tout and time.time() > deadline:
				raise RuntimeError('%s timeout (%f sec) waiting status %#x/%#x, current status %#x' %
					(self, tout, set_bits & 0xffff, clr_bits & 0xffff, st))

	def wait_ready(self, tout = None):
		"""Wait ready status (after reset or srq)"""
		return self.wait_status(STATUS.ready, ~STATUS.ready, tout)

	def trigger(self, what):
		"""Trigger action"""
		self.poke(TBMCDev.wr_triggers, 1 << what)

	def configure_chans(self, channels):
		"""Setup the number of active channels"""
		self.poke(TBMCDev.wr_cfg_ctl, channels - 1)

	def configure_freq(self, div, interval, xinterval):
		"""
		Setup the bus clock divider and byte transmission intervals
		in usec for normal and fast transmission modes.
		The resulting bus clock frequency will be 25/(div+1) MHz. 
		"""
		assert 0 <= div and div < 256
		assert 0 < interval and interval < 256
		assert 0 < xinterval and xinterval < 256
		self.poke(TBMCDev.wr_freq_ctl, div | (interval << 8) | (xinterval << 24))

	def configure_rst(self, rst_time, rst_hold):
		"""Setup reset parameters - reset time and clock hold time for hard reset, both in usec."""
		assert 0 < rst_time and rst_time < 256
		assert 0 < rst_hold and rst_hold < 256
		self.poke(TBMCDev.wr_rst_ctl, rst_time | (rst_hold << 8))

	def configure_tx(self, cmd_length, tx_fast = False, b16 = False, loop = False):
		"""Setup transmit parameters - command length, fast mode, 16 bit mode and looping mode for self testing"""
		assert 0 < cmd_length and cmd_length <= TBMCDev.max_cmd_length
		v = cmd_length - 1
		if tx_fast : v |= 1 << 10
		if b16     : v |= 1 << 11
		if loop    : v |= 1 << 15
		self.poke(TBMCDev.wr_cmd_ctl, v)

	def configure_rx(self, rx_length, skip = 0, wait = False, loopback = False):
		"""
		Setup receive parameters - the response length, wait non-zero response flag,
		streaming mode and loopback flag used for self testing. The streaming mode will be set if response length
		argument is zero. In such case the receiving must be stopped explicitly by sending TRIG.stop
		"""
		assert 0 <= rx_length and rx_length <= TBMCDev.max_rx_length
		v = rx_length - 1 if rx_length > 0 else 1 << 14
		if wait     : v |= 1 << 13
		if loopback : v |= 1 << 15
		self.poke(TBMCDev.wr_rx_ctl, v | (skip << 16))

	def cmd_put(self, buff):
		"""Write command string to the command buffer"""
		sz = len(buff)
		if sz % 2:
			buff += '\0'
			sz += 1
		assert 0 < sz and sz <= TBMCDev.max_cmd_length
		self.write16(TBMCDev.wr_cmd_buff, buff)

	def rx_buff_read(self, sz):
		"""Read data from the receiver buffer"""
		sz_ = sz
		# Round to 4 bytes boundary Note that you can read any number
		# of bytes past the end of the buffer. They will be zero.
		if sz_ & 3: sz_ += 4 - (sz_ & 3)
		buff = self.read(TBMCDev.rd_rx_buff, sz_)
		return buff[0:sz]

	def rx_buff_read_all(self, sz, chs):
		"""Read data from the receiver buffer for all channels"""
		sz_ = sz
		if sz_ % 2: sz_ += 1
		assert 0 < sz_ and sz_ <= TBMCDev.max_rx_length
		buff = self.rx_buff_read(sz_ * chs)
		return [str(buff[i*sz_:i*sz_+sz]) for i in range(chs)]
