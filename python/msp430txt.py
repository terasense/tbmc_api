# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: MSP430 text code format loader
#
# Author: Oleg Volkov olegv142@gmail.com

def load(fd):
	"""
	Load segments from the specified file descriptor.
	Returns the list of (addr, code) tuples.
	"""
	segs = []
	addr = None
	data = None
	ls = fd.readlines()
	try:
		for l in ls:
			if l[0] == '@':
				if addr != None:
					segs += (addr, data)
				addr = int(l[1:], base=16)
				data = ''
			elif l[0] == 'q':
				if addr is None:
					return None
				segs.append((addr, data),)
				return segs
			else:
				bytes = l.split()
				for b in bytes:
					data += chr(int(b, base=16))
	except:
		pass
	return None

def load_file(path):
	"""Load specified file"""
	try:
		with open(path) as f:
			return load(f)
	except:
		return None
