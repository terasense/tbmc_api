#
# T-BUS configuration file
#

# The number of active channels
nchannels = 8

# Bus bit frequency in Hz. It must divide the controller master clock = 25MHz.
tbus_freq = 2500000

#
# The following idle intervals are expressed in units equal to 1/2 bus clock period.
# They must be greater than 0 and less than 256
#

# The byte transmission idle interval
tbus_tx_idle = 128

# The byte transmission idle interval in turbo mode
tbus_turbo_idle = 32

# The byte transmission idle interval during wait
tbus_wt_idle = 255

# Use turbo mode
tbus_turbo = True

# Use 16 bit mode
tbus_16bit_mode = True

# Skip command cookies to improve performance
skip_cmd_cookies = True

# Skip SQR status check to improve performance
skip_srq_status_check = True

