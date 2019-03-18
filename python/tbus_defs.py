# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: T-BUS protocol related definitions
#
# Author: Oleg Volkov olegv142@gmail.com

import struct

# Command flags
cmd_has_data_      = 8
cmd_mult_response_ = 4

# Command codes
cmd_enum  = 1					# Increment r_cnt and pass, no data
cmd_wait  = cmd_enum  + 1		# Similar to NOP but wait for async operation completion before passing command to next module
cmd_test  = cmd_has_data_		# Just pass data untouched
cmd_write = cmd_test  + 1		# Write data to the target memory
cmd_poll  = cmd_write + 1		# Poll target memory bits. The memory size is half the size of data. The first data byte
								# will be OR-ed with memory byte, the next byte will be AND-ed with the same byte and so on.
cmd_read  = cmd_has_data_ | cmd_mult_response_	# Increment r_cnt and append (len1 + 1) bytes to data

# Command names
cmd_names = {
	cmd_enum  : 'ENUM', 
	cmd_wait  : 'WAIT',
	cmd_test  : 'TEST',
	cmd_write : 'WRITE',
	cmd_poll  : 'POLL',
	cmd_read  : 'READ',
}

# Command header format
hdr_fmt = 'BBHBBH'
hdr_sz  = struct.calcsize(hdr_fmt)

# Data length encoding
data_length_bits = 8
max_data_length  = (1 << data_length_bits)

# Fatal errors bit mask
cmd_err_flags    = 0xf

