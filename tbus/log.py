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
level = l_inf

# Output file
file = sys.stderr

#
# Output functions
#
def msg(l, s, a = None):
	if level >= l:
		if a:
			print >> file, s % a
		else:	
			print >> file, s

def msg_(l, s, a = None):
	if level >= l:
		if a:
			print >> file, s % a,
		else:	
			print >> file, s,

def err (s, *a): msg (l_err, s, a)
def err_(s, *a): msg_(l_err, s, a)

def warn (s, *a): msg (l_warn, s, a)
def warn_(s, *a): msg_(l_warn, s, a)

def inf (s, *a): msg (l_inf, s, a)
def inf_(s, *a): msg_(l_inf, s, a)

def notice (s, *a): msg (l_notice, s, a)
def notice_(s, *a): msg_(l_notice, s, a)

def dbg (s, *a): msg (l_dbg, s, a)
def dbg_(s, *a): msg_(l_dbg, s, a)

def trc (s, *a): msg (l_trc, s, a)
def trc_(s, *a): msg_(l_trc, s, a)

