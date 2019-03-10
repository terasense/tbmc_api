# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The memory mapped device communication helper
#
# Author: Oleg Volkov olegv142@gmail.com

import os.path
import glob
import ctypes
import mmap
import mmio

class MmDev:
	def __init__(self, name, cls = 'amba_pl'):
		"""Open device given its name"""
		self.name = name
		for path in glob.glob('/proc/device-tree/' + cls + '/' + name + '@*'):
			n, addr = os.path.basename(path).split('@')
			assert n == name
			self.addr = int(addr, 16)			
			break
		else:
			raise RuntimeError(name + 'not found')

		assert self.addr % 4096 == 0
		with open('/dev/mem', 'r+') as f:
			self.map = mmap.mmap(f.fileno(), 4096, offset=self.addr)

	def __str__(self):
		return '%s@%x' % (self.name, self.addr)

	def peek(self, reg):
		"""Peek 32 bit value from the device register given its index"""
		return mmio.peek(ctypes.pointer(ctypes.c_uint.from_buffer(self.map, 4*reg)))

	def poke(self, reg, val):
		"""Poke 32 bit value to the device register given its index"""
		r = mmio.poke(ctypes.pointer(ctypes.c_uint.from_buffer(self.map, 4*reg)), val)
		assert r == 0

	def read(self, reg, sz):
		assert sz & 3 == 0
		buff = ctypes.create_string_buffer(sz)
		r = mmio.read(
				ctypes.pointer(ctypes.c_uint.from_buffer(self.map, 4*reg)),
				ctypes.pointer(ctypes.c_uint.from_buffer(buff)),
				sz >> 2
			)
		assert r == 0
		return buff

	def write(self, reg, str):
		sz = len(str)
		if (sz & 3) != 0:
			sz += 4 - (sz & 3)
		buff = ctypes.create_string_buffer(str, sz)
		r = mmio.write(
				ctypes.pointer(ctypes.c_uint.from_buffer(self.map, 4*reg)),
				ctypes.pointer(ctypes.c_uint.from_buffer(buff)),
				sz >> 2
			)
		assert r == 0

	def write16(self, reg, str):
		sz = len(str)
		if (sz & 1) != 0:
			sz += 2 - (sz & 1)
		buff = ctypes.create_string_buffer(str, sz)
		r = mmio.write16(
				ctypes.pointer(ctypes.c_uint.from_buffer(self.map, 4*reg)),
				ctypes.pointer(ctypes.c_ushort.from_buffer(buff)),
				sz >> 1
			)
		assert r == 0
