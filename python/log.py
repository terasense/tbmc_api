# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: Simple logging helper
#
# Author: Oleg Volkov olegv142@gmail.com

import sys

# Log levels
l_err    = -2
l_warn   = -1
l_inf    = 0
l_notice = 1
l_dbg    = 2
l_trc    = 3

# Current verbosity level
verbose = l_inf

# Output functions

def err(s):
	print >> sys.stderr, s

def warn(s):
	if verbose >= l_warn:
		print >> sys.stderr, s

def msg(l, s):
	if verbose >= l:
		print >> sys.stderr, s

def msg_(l, s):
	if verbose >= l:
		print >> sys.stderr, s,

def inf(s): msg(l_inf, s)
def inf_(s): msg_(l_inf, s)
def notice(s): msg(l_notice, s)
def notice_(s): msg_(l_notice, s)
def dbg(s): msg(l_dbg, s)
def trc(s): msg(l_trc, s)

