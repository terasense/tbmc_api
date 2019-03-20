# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: T-MODULE access helpers
#
# Author: Oleg Volkov olegv142@gmail.com

import time
import struct
import tmod_defs as tm
import log

def read_version(ctl):
	"""Read system version as (version, hw_id) tuple. Returns (r_cnt, data) tuple."""
	r = ctl.bus_read_struct_coherent(tm.status_addr, 'BB')
	return r

def read_status(ctl):
	"""Read system status as (version, hw_id, system_flags, srq_status, code_chksum) tuple. Returns (r_cnt, data) tuple."""
	r = ctl.bus_read_struct_coherent(tm.status_addr, 'BBBBI')
	return r

def read_srq_status(ctl):
	"""Read srq status as (status) tuple. Returns (r_cnt, data) tuple."""
	return ctl.bus_read_struct_coherent(tm.status_addr + 3, 'B')

def read_code_chksum(ctl):
	"""Read code buffer checksum as (code_chksum) tuple. Returns (r_cnt, data) tuple."""
	return ctl.bus_read_struct_coherent(tm.status_addr + 4, 'I')

def reset(ctl):
	"""Reset controller"""
	for a in ('last_srq', 'skip_srq_status_check'):
		if hasattr(ctl, a):
			delattr(ctl, a)
	ctl.bus_reset()

def srq(ctl, req_code, param = 0, addr = 0, data = None):
	"""Issue SRQ"""
	log.dbg("srq #%d", req_code)
	if getattr(ctl, 'last_srq', None) != (req_code, param, addr, data):
		hdr = struct.pack('BBH', req_code, param, addr)
		if data is not None:
			hdr += data
		ctl.bus_write(tm.srq_addr, hdr)
		ctl.last_srq = (req_code, param, addr, data)

	ctl.bus_srq()

def srq_sync(ctl, req_code, param = 0, addr = 0, data = None, delay = 0):
	"""Issue SRQ, wait completion and check status"""
	sync_mode = ctl.mod_version > 0x10
	if sync_mode:
		req_code |= tm.srq_sync
	srq(ctl, req_code, param, addr, data)
	if not sync_mode:
		if delay:
			time.sleep(delay)
		if req_code == tm.srq_proc:
			ctl.bus_wait()
	skip_status_check = getattr(ctl, 'skip_srq_status_check', False)
	if not skip_status_check:
		r = read_srq_status(ctl)
		if r[1][0] != tm.SRQ_SUCCESS:
			raise RuntimeError('SRQ %d is failed on all modules with status %#x (%s)'
				% (req_code, r[1][0], tm.srq_status_names.get(r[1][0], '???')))
	ctl.skip_srq_status_check = ctl.cfg.skip_srq_status_check

def program(ctl, addr, data):
	"""Write code to the code buffer"""
	off, total, chksum = 0, len(data), tm.get_chksum(data)

	assert total > 0
	assert (addr % tm.seg_size) == 0

	while off < total:
		chunk = total - off
		if chunk > tm.srq_buff_chunk:
			chunk = tm.srq_buff_chunk
		srq_sync(ctl, tm.srq_flash_ers_wrt if not off else tm.srq_flash_wrt, chunk, addr, data[off:off+chunk])
		off  += chunk
		addr += chunk

	r = read_code_chksum(ctl)
	if r[1][0] != chksum:
		raise RuntimeError('Check sum mismatch: reported %08x, expected %08x' % (r[1][0], chksum))
