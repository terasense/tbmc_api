#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: Web server
#
# Author: Oleg Volkov olegv142@gmail.com

import sys, base64, json
#from SocketServer import TCPServer, ThreadingMixIn
#from SimpleHTTPServer import SimpleHTTPRequestHandler
#from urlparse import urlparse

sys.path.append('..')
from tbus import tbmc_dev, tbus_ctl, ts32, pixels
import tbus.config.tbus_conf as tbus_conf
import tbus.config.ts32_conf as applet_conf

ctl = tbus_ctl.TBUSCtl(tbmc_dev.TBMCDev(), tbus_conf)
ctl.bus_init()
ts32.configure(ctl, applet_conf)

data = ts32.acquire(ctl, applet_conf)
pixs = pixels.get_image_pixels(data)
h, w = pixs.shape

print json.dumps({'height': h, 'width': w})
print pixs
print base64.b64encode(pixs)
