# -*- coding: utf-8 -*-
#
# $Id: uckParamsEditor.py,v 2.1 2010-02-22 09:19:01 wjg Exp $
#
# NAME:
#	uckParamsEditor.py -- Parameter Editor for uckFlow
#
# DESCRIPTION:
#	This module implements a simpe editor that can be used to edit
#	uckFlow parameter files.
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

import sys
import os
import pygtk
pygtk.require("2.0")
import gobject
import gtk
import gtk.glade

from uckProject import Project
from uckDialogs import ErrorDialog, InfoDialog, ConfirmDialog

# message localization support
APP = "uckFlow"
DIR = "locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

# Remove newlines and extra spaces from a string
def denl(s):
	s = s.expandtabs()
	s = s.replace('\n', ' ')
	while s.find("  ") >= 0:
		s = s.replace("  ", ' ')
	return s

class UckParam:
	"""The display part for an UCK parameter. This consists of a
	VBox containing a TextView for the comment and a TextEntry
	for the value. All of that is displayed within a Notebook tab.
	"""

	def __init__(self, obj):
		self.cfgObject = obj
		self.changed = False

		# Create the optical representation (bottom to top)
		#	valueTextEntry
		self.valueEntry = gtk.Entry()
		self.valueEntry.set_text(obj.get_value())
		self.valueEntry.set_editable(not obj.is_readonly())
		self.valueEntry.set_sensitive(not obj.is_readonly())
		#	within an unnamed Frame
		valueFrame = gtk.Frame(_("Value"))
		valueFrame.add(self.valueEntry)
		#	commentTextBuffer
		self.commentTextBuffer = gtk.TextBuffer()
		self.commentTextBuffer.set_text(denl(obj.get_comment()))
		self.commentView = gtk.TextView(self.commentTextBuffer)
		self.commentView.set_wrap_mode(gtk.WRAP_WORD)
		#	within an unnamed Frame
		commentFrame = gtk.Frame(_("Comment"))
		commentFrame.add(self.commentView)
		#	vbox container
		self.vbox = gtk.VBox()
		self.vbox.pack_start(commentFrame, True, True, 8)
		self.vbox.pack_start(valueFrame, False, False, 8)
		# FIXME: add callbacks when text is changed

	# Extract the representation widget
	def get_rep(self):
		return self.vbox

	# Extract the configuration object
	def get_obj(self):
		return self.cfgObject

	# Commit changes from entry fields to the object
	def commit(self):
		if self.changed:
			n = self.commentTextBuffer.get_text()
			# FIXME: word-wrap and insert newlines!
			self.cfgObject.set_comment(n)
			n = self.valueEntry.get_text()
			self.cfgObject.set_value(n)
			# FIXME: Should we write cfg back to file at this point?
		self.changed = False

	# Reset comment & value from cfgObject
	def reset(self):
		self.valueEntry.set_text(self.cfgObject.get_comment())
		self.commentTextBuffer.set_text(denl(self.cfgObject.get_value()))
		self.changed = False

	def get_name(self):
		return self.cfgObject.get_name()

	def is_readonly(self):
		return self.cfgObject.is_readonly()

	def can_be_deleted(self):
		return self.cfgObject.can_be_deleted()

class UckParamEditor:
	"""The uckFlow parameter editor
	"""
	
	def __init__(self):
		# Set the Glade file (found in module directory)
		self.dir = os.path.dirname(__file__)
		self.gladefile = os.path.join(self.dir, "uckFlow.glade")
		self.wTree = gtk.glade.XML(self.gladefile, "uckParamsEditor") 
		self.topLevel = self.wTree.get_widget("uckParamsEditor")
		self.notebook = self.wTree.get_widget("uckParamsNotebook")

		# Create dictionary of callbacks and autoconnect them
		dic = {
		# FIXME: connect Add, Remove, Cancel, OK callbacks
		"on_uckParamsEditor_destroy" : self.quit }
		self.wTree.signal_autoconnect(dic)


	# Show the parameter editor
	def show(self):
		self.reset()
		project = Project.get_instance().project
		for name, value in project.iteritems():
			item = UckParam(value)
			if value.is_readonly():
				tab_label = value.get_name()
			else:
				tab_label = "<b>" + value.get_name() + "</b>"
			label = gtk.Label(tab_label)
			label.set_use_markup(True)
			self.notebook.append_page(item.get_rep(), label)
		self.topLevel.show_all()

	# Reset everything to a known state
	def reset(self):
		self.topLevel.hide()
		while self.notebook.get_n_pages() > 0:
			self.notebook.remove_page(0)

	# Terminate the application FIXME: warn if changes not committed
	def quit(self, widget = None):
		self.reset()

	# FIXME: Parameter attributes - Comment editable! Word wrap at 80
	# FIXME: Callbacks - add / implement
	# FIXME: 
