# (C) 2018-2019 TeraSense Inc. http://terasense.com/
# All Rights Reserved
#
# Description: The bunch of properties holder object (aka bunch pattern)
#
# Author: Oleg Volkov olegv142@gmail.com

class Bunch(dict):
	def __init__(self, *args, **kwargs):
		super(Bunch, self).__init__(*args, **kwargs)
		self.__dict__ = self

