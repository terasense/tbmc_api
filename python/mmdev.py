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
			raise RuntimeError(name + ' not found')

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
		"""Read data buffer from 32 bit wide device register given its index"""
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
		"""Write data buffer to 32 bit wide device register given its index"""
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
		"""Write data buffer to 16 bit wide device register given its index"""
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

	def read_ex(self, reg, sz, prefix = None, skipz = 0):
		"""
		Read data buffer from 32 bit wide device register given its index.
		The caller may optionally provide the prefix of the buffer which is already read.
		If skipz parameter is not zero the leading zero 16 bit words will be skipped on read
		until either first non-zero word will be read or the number of 32 bit words read reach
		skipz parameter value. In the latter case the function return the number of bytes read
		equal to zero. The routine returns the pair of buffer and the number of bytes read
		(including prefix). Since data is read by 32 byte words the size of the data actually read
		may exceed size requested in sz parameter. The suiffix may be passed as prefix parameter to
		the next call to this routine.
		"""
		assert sz & 1 == 0
		assert not (prefix is not None and sipz)
		if prefix is not None:
			buff = ctypes.create_string_buffer(prefix, sz + 2)
			plen = len(prefix)
			assert plen & 1 == 0
			assert plen < sz
		else:
			buff = ctypes.create_string_buffer(sz + 2)
			plen = 0
		r = mmio.read16_ex(
				ctypes.pointer(ctypes.c_uint.from_buffer(self.map, 4*reg)),
				ctypes.pointer(ctypes.c_ushort.from_buffer(buff, plen)),
				(sz - plen) >> 1, skipz
			)
		assert r >= 0
		r <<= 1
		assert r >= sz - plen or r == 0
		assert r <= sz - plen + 2
		assert r != 0 or skipz
		return buff, plen + r

