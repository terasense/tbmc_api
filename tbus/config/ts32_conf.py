#
# TS32 data acquisition config
# The module master clock frequency is 4MHz
#

# The path to the code
code_path = '../applets/ts32b2.txt'

# ADC clock divider.
#  0: /1, .. , 6: /7, 7: /8
adc_clk_div = 3 # 1MHz 12usec conv time

# ADC sample and hold time in ADC clock units
#  0: 4, 1: 8, 2: 16, 3: 64
adc_sh_time = 1 # 8usec

# Timer clock divider
#  0: /1, 1: /2, 2: /4, 3: /8
timer_clk_div = 1 # 2MHz

# Frame time in timer clock periods
#  0: 2^16, 1: 2^15, .. , 7: 2^9
timer_frame = 7 # 256usec

# The integration time in timer clock periods
int_time = 250 # 125usec

# Reset time in timer clock periods
#  0: frame/2, 1: frame/4, .. , 7: frame/2^8
reset_time = 2 # last 1/8 of the frame

# Set to 1 to disable double sampling
no_cdc = 0

# Set to 1 to measure internal temperature sensor output instead of real input
temp_test = 0

# Set to 1 to use full VCC as reference
vcc_ref = 0

# Wait before reading results (sec)
read_delay = 0

# Note that the applet report error if integration time + conversion time exceeds the frame time - reset time
# The output data order is the following:
#  0        value measured with integrator off
#  1        value measured with zero input
#  2        value measured with test input
#  3 .. 34  values from channels 0 .. 31 measured
