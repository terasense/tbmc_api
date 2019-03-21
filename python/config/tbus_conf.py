#
# T-BUS configuration file
#

# The number of active channels
nchannels = 8

# Bus clock frequency divider. Divide the controller master clock (25MHz) to produce bit clock for SPI buses.
tbus_clk_div = 6

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

#
# Optimization settings
#

# Skip command cookies to improve performance
skip_cmd_cookies = True

# Skip SQR status check to improve performance
skip_srq_status_check = True

