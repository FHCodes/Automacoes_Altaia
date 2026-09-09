#!/usr/bin/env python

__doc__ = \
'''
	The purpose of this object is to provide an interface that allows the object to be divided in order to be distributed to different instances of the same obects for asynchronous processing
'''

__version__ = '0.1'

__authors__ = [
				"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
			]

import abc


class SplittableObject(object):

	__metaclass__ = abc.ABCMeta

	# Class Constructor
	def __init__(self):
		pass

	def chunks(self, l, n):
		"""
			Yield successive n-sized chunks from l.
		"""
		for i in xrange(0, len(l), n):
			yield l[i:i+n]

	def divideInSublists(self, l, n):
		"""
			Divide all objects in l progressively by a list of n lists
		"""

		divided = [ [] for i in range(n)]
		i = 0

		for elem in l:

			divided[i].append(elem)

			i += 1
			# When the end of the main list is reached, start from beginning
			if i == n:
				i = 0

		return divided

	@abc.abstractmethod
	def splitObject(self, nObjects):
		"""
			An object that implements this method, is supposed to divide itself in nObjects equivalent instances.
			Useful for containers with lists.
			Returns a list containing nObjects equivalent instances of the split object.
		"""
		pass
