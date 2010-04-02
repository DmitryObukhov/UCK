# -*- coding: utf-8 -*-
#
# $Id: StaticMethod.py,v 2.1 2010-02-22 09:19:00 wjg Exp $
#
# NAME:
#	StaticMethod -- python way to define class methods
#
# DESCRIPTION:
#	This encapsulates the python way of creating static methods
#	aka. class methods
#
# ORIGIN:
#	http://code.activestate.com/recipes/52304/
#
# USE:
#	Define a method within the class without the self argument and
#	then wrap the method with StaticMethod, i.e.:
#
#	class aClass:
#		def static_method(argument):
#			... # Do whatever. May (obviously) not use self!
#		static_method = StaticMethod(static_method)
#
#	By convention use the same name for the method and the callable,
#	thus rendering the method inaccessible except through the wrapper.
class StaticMethod:
	def __init__(self, callable):
		self.__call__ = callable
