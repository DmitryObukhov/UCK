# -*- coding: utf-8 -*-
#
# $Id$
#
# NAME:
#	uckDialog.py -- dialogs from uckFlow
#
# DESCRIPTION:
#	This module contains all the standard dialogs needed in applications.
#
# AUTHOR:
#	Wolf Geldmacher, wolf <at> womaro.ch, http.//www.womaro.ch
#
# COPYRIGHT:
#	Copyright © 2010, The UCK Team
#
# LICENSE:
#	uckFlow is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	uckFlow is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with uckFlow.  If not, see <http://www.gnu.org/licenses/>.
import pygtk
pygtk.require("2.0")
import gtk

class InfoDialog:
	"""This class creates a modal message dialog, runs and then destroys it.
	"""
	def __init__(self, message, parent = None):
		md = gtk.MessageDialog(parent,
			gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, 
			gtk.BUTTONS_CLOSE, message)
		md.run()
		md.destroy()

class ConfirmDialog:
	"""This class creates a modal confirm dialog, runs and then destroys it.
	"""
	def __init__(self, message, parent = None):
		md = gtk.MessageDialog(parent,
			gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, 
			gtk.BUTTONS_OK|gtk.BUTTONS_CLOSE, message)
		answer = md.run()
		md.destroy()
		return answer

class WarnDialog:
	"""This class creates a modal warn dialog, runs and then destroys it.
	"""
	def __init__(self, message, parent = None):
		md = gtk.MessageDialog(parent,
			gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, 
			gtk.BUTTONS_CLOSE, message)
		md.run()
		md.destroy()

class ErrorDialog:
	"""This class creates a modal error dialog, runs and then destroys it.
	"""
	def __init__(self, message, parent = None):
		md = gtk.MessageDialog(parent,
			gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, 
			gtk.BUTTONS_CLOSE, message)
		md.run()
		md.destroy()
