#!/usr/bin/python2

# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: Web server
#
# Author: Oleg Volkov olegv142@gmail.com

import sys, os, base64, json
from SocketServer import TCPServer, ThreadingMixIn
from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse

cur_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(cur_dir, '..'))

from tbus import tbmc_dev, tbus_ctl, ts32, pixels
import tbus.config.tbus_conf as tbus_conf
import tbus.config.ts32_conf as applet_conf

PORT = 80

class HttpHandler(SimpleHTTPRequestHandler):
	protocol_version = 'HTTP/2.0'

	def getEventsStream(self):
		ctl = tbus_ctl.TBUSCtl(tbmc_dev.TBMCDev(), tbus_conf)
		ctl.bus_init()
		ts32.configure(ctl, applet_conf)

		data = ts32.acquire(ctl, applet_conf)
		pixs = pixels.get_image_pixels(data)
		h, w = pixs.shape

		self.send_response(200)
		self.send_header('Cache-Control', 'no-cache')
		self.send_header('Content-Type','text/event-stream')
		self.end_headers()

		self.wfile.write('event: setup\r\n')
		self.wfile.write('data: %s\r\n' % json.dumps({'height': h, 'width': w}))
		self.wfile.write('\r\n')

		ts32.run_auto(ctl)

		while True:
			self.wfile.write('event: frame\r\n')
			self.wfile.write('data: %s\r\n' % base64.b64encode(pixs))
			self.wfile.write('\r\n')

			data = ts32.acquire_auto(ctl)
			pixs = pixels.get_image_pixels(data)

	def do_GET(self):
		url = urlparse(self.path)
		if url.path == '/stream':
			return self.getEventsStream()
		SimpleHTTPRequestHandler.do_GET(self)

def start():
	web_dir = os.path.join(cur_dir, 'www')
	os.chdir(web_dir)

	httpd = TCPServer(("", PORT), HttpHandler)
	print "serving at port", PORT
	httpd.serve_forever()

if __name__ == '__main__':
	start()


