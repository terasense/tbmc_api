# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The memory mapped IO helper
#
# Author: Oleg Volkov olegv142@gmail.com

from ctypes import *

#
# libmmio is simple library exporting the following functions
# 
# uint32_t mm_peek(uint32_t const* addr)
# int mm_poke(uint32_t* addr, uint32_t val)
# int mm_read(uint32_t const* addr, uint32_t* buff, unsigned word_cnt)
# int mm_write(uint32_t* addr, uint32_t const* buff, unsigned word_cnt)
# int mm_write16(uint32_t* addr, uint16_t const* buff, unsigned word_cnt)

libmmio = CDLL('libmmio.so.1.0')

peek    = libmmio.mm_peek
poke    = libmmio.mm_poke
read    = libmmio.mm_read
write   = libmmio.mm_write
write16 = libmmio.mm_write16

peek.argtypes = [POINTER(c_uint)]
peek.restype = c_uint
poke.argtypes = [POINTER(c_uint), c_uint]
read.argtypes = [POINTER(c_uint), POINTER(c_uint), c_uint]
write.argtypes = [POINTER(c_uint), POINTER(c_uint), c_uint]
write16.argtypes = [POINTER(c_uint), POINTER(c_ushort), c_uint]
