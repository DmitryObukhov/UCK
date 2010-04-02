# -*- coding: utf-8 -*-
#
# $Id$
#
# NAME:
#	uckFlowLog -- the uckFlowLog handler
#
# DESCRIPTION:
#	Handling of the logfile window.
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

import os
import sys
import subprocess
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade

from uckProject import Project
from uckExecutor import Executor

# Create uckFlowLog GUI from glade description and perform actions
class UckFlowLog:
	"""This is the UckFlowLog dialog"""

	def __init__(self, gladefile):
		self.gladefile = gladefile
		self.logfile = None
		self.command = None
		self.follow = False

		# Get the dialog from the glade file
		self.wTree = gtk.glade.XML(self.gladefile, "uckFlowLog") 
		self.logDialog = self.wTree.get_widget("uckFlowLog")
		self.textView = self.wTree.get_widget("logDialogTextView");
		self.logDialogFollow = self.wTree.get_widget("logDialogFollowCheckButton")
		self.textBuffer = gtk.TextBuffer()
		end = self.textBuffer.get_end_iter()
		self.endMark = self.textBuffer.create_mark("end", end, False)
		self.textView.set_buffer(self.textBuffer)
		self.textView.set_cursor_visible(False)
		self.clear()

		# Create dictionary of callbacks and autoconnect them
		dic = {
			"on_logDialogFollowCheckButton_toggled" : self.toggle_follow,
			"on_logDialogClearButton_clicked" : self.clear,
			"on_logDialogCloseButton_clicked" : self.hide,
			"on_uckFlowLog_delete" : self.hide,
		}
		self.wTree.signal_autoconnect(dic)
		self.hide()

	# Clear the text buffer
	def clear(self, widget = None):
		self.textBuffer.set_text("");

	# Follow log toggle
	def toggle_follow(self, widget):
		self.follow = self.logDialogFollow.get_active()

	# Show the dialog
	def show(self):
		self.logDialog.show_all()

	# Hide the dialog
	def hide(self, widget = None, whatever = None):
		self.logDialog.hide()
		return True

	# Set the name of the file to follow
	def set_logfile(self, logfile = None):
		# If logfile name is unchanged do nothing
		if self.logfile == logfile:
			return

		# Check the existence of the logfile
		if logfile and not os.path.isfile(logfile):
			return

		# Remember the logfile name
		self.logfile = logfile

		# Abort tail command, iff running
		if self.command:
			self.command.abort()

		# Create executor to follow the logfile
		if logfile:
			self.command = Executor("tail", logfile,
					self.append, self._end)

		# Clear old contents, iff any
		self.clear()

	# Called when there is some more input from the tail command
	def append(self, text):
		end = self.textBuffer.get_iter_at_mark(self.endMark)
		self.textBuffer.insert(end, text)
		if self.follow:
			self.textView.scroll_mark_onscreen(self.endMark)

	# Called when the tail command ends.
	#	Ignore status, just cleanup.
	def _end(self, status):
		self.command = None
		self.logfile = None
		self.clear()
		self.hide()
