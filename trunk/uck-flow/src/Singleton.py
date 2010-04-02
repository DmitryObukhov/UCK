# -*- coding: utf-8 -*-
#
# $Id$
#
# NAME:
#	Singleton -- Singleton base class
#
# DESCRIPTION:
#	The "Singleton" pattern creates a single instance of a class.
#
#	This specific implementation allows the constructor to be called
#	multiple times, but the same (single) instance will be returned
#	each time and (optional) parameters to the constructor will be
#	ignored (except for the first instantiation).
#
# ORIGIN:
#	http://code.activestate.com/recipes/66531/
#
# USE:
#	Just derive a class from this base.
class Singleton(object):
	def __new__(cls, *p, **k):
		if not '_the_instance' in cls.__dict__:
			cls._the_instance = object.__new__(cls)
		return cls._the_instance
