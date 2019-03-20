# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: TS32 data to image conversion helper
#
# Author: Oleg Volkov olegv142@gmail.com

import numpy as np
import config.pix_conf as pconf

pmap = None

def build_pixels_map(nmodules):
	"""Build module / channel to pixel mapping"""
	global pmap
	assert nmodules % pconf.modules_in_row == 0

	sensor_width  = pconf.modules_in_row * pconf.mod_w
	sensor_height = (nmodules / pconf.modules_in_row) * pconf.mod_h

	# The module index for every image pixel
	m_ind = np.empty((sensor_height, sensor_width), dtype=int)
	# The channel index for every image pixel
	c_ind = np.empty((sensor_height, sensor_width), dtype=int)

	for r in range(sensor_height):
		for c in range(sensor_width):
			m_ind[r, c], (mr, mc) = pconf.mod_resolver(r, c, nmodules)
			assert mr <= r and mc <= c
			c_ind[r, c] = pconf.mod_pixels[r - mr][c - mc]

	if pconf.image_fliplr:
		m_ind, c_ind = np.fliplr(m_ind), np.fliplr(c_ind)
	if pconf.image_flipud:
		m_ind, c_ind = np.flipud(m_ind), np.flipud(c_ind)
	if pconf.image_transpose:
		m_ind, c_ind = np.transpose(m_ind), np.transpose(c_ind)

	pmap = (m_ind, c_ind)

def get_image_pixels(data):
	"""Convert data array to image array according to pixels config"""
	if pmap is None:
		build_pixels_map(data.shape[0])

	m_ind, c_ind = pmap
	return pconf.channel_data(data, m_ind, c_ind)

