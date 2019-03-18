# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: T-MODULE related definitions
#
# Author: Oleg Volkov olegv142@gmail.com

#
# Addresses
#
ram_base      = 0x200
status_addr   = ram_base
temp_addr     = status_addr + 8
srq_addr      = ram_base + 10
srq_buff_addr = srq_addr + 4

# The recommended data chunk size for writing onto the buffer
# Guaranteed to fit to the buffer on all hardware
srq_buff_chunk_bits = 6
srq_buff_chunk  = (1 << srq_buff_chunk_bits)

# Flash segment size
seg_bits = 9
seg_size = (1 << seg_bits)

#
# System status flags
#
hard_reset         = 0x1
clock_uncalibrated = 0x2
srq_pending        = 0x4
chksum_valid       = 0x8
tbus_err           = 0x10
sys_err            = 0x20

#
# SRQ request codes
#
srq_none          = 0
srq_flash_ers     = 1
srq_flash_wrt     = 2
srq_flash_ers_wrt = (srq_flash_ers | srq_flash_wrt)
srq_proc          = 4
srq_sync          = 0x80

#
# SRQ status
#
SRQ_SUCCESS			= 0
# ...
# Application specific codes here
# ...
SRQ_FAILED			= 0xf0 # Generic error
SRQ_INVALID			= 0xf1 # Invalid parameters
SRQ_NOT_CONFIGURED	= 0xfe # SRQ was not configured
SRQ_UNKNOWN			= 0xff # Status unknown

# SRQ status names
srq_status_names = {
	SRQ_SUCCESS        : 'success',
	SRQ_FAILED         : 'failed',
	SRQ_INVALID        : 'invalid',
	SRQ_NOT_CONFIGURED : 'not configured',
	SRQ_UNKNOWN        : 'unknown'
}

#
# Helper routines
#

def get_abs_temp(val):
	"""Returns absolute temperature (K) given the 10 bit ADC reading with 1.5V reference"""
	return 404 * val / 1024

def get_chksum(data):
	"""Calculate data check sum using the same algorithm as module"""
	h, a = 5381, 0
	#
	# We are using the most simple algorithm but make sure
	# the trailing 0xff in the erased flash content does not
	# affect the calculation result (though not trailing does)
	#
	for c in data:
		val = ~ord(c) & 0xff
		h = (33*h + val) & 0xffff # DJB hash
		if val:
			a = a + h
			a = ((a >> 8) & 0xffffff) | ((a & 0xff) << 24)

	return a

