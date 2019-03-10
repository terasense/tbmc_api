# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The TBMC memory mapped device communication helper
#
# Author: Oleg Volkov olegv142@gmail.com

from mmdev import MmDev

class TBMCDev(MmDev):
	name = 'axi_tbmc'
	magic = 0x4f56

	def __init__(self):
		MmDev.__init__(self, TBMCDev.name)
		v = self.peek(0)
		assert v >> 16 == TBMCDev.magic
		self.channels = 1 + (v & ((1 << 10) - 1))
		self.version = (v & ((1 << 16) - 1)) >> 10

	def __str__(self):
		return '%s v.%d %d channels' % (
				TBMCDev.name, self.version, self.channels
			)

