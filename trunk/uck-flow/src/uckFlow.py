# -*- coding: utf-8 -*-
#
# $Id$
#
# NAME:
#	uckFlow.py -- main logic of the uckFlow tool
#
# DESCRIPTION:
#	This module is the "pièce de résistance" of uckFlow. It creates the
#	GUI from the glade description, handles user interaction and
#	sequencing through the lict of selected actions.
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

from stat import ST_MTIME
from time import strftime

from uckProject import Project
from uckExecutor import Executor
from uckDialogs import ErrorDialog, InfoDialog
from uckFlowLog import UckFlowLog

# message localization support
APP = "uckFlow"
DIR = "locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext
# Localization initialization for glade:
for module in (gettext, gtk.glade):
	module.bindtextdomain(APP, DIR)
	module.textdomain(APP)

class Action:
	"""This class defines an action and handles interaction between
	the associated CheckButton and Image used to display success or
	failure.
	"""

	def __init__(self, wtree, action):
		self.wTree = wtree
		self.action = action
		toggleName = action + "CheckButton"
		self.toggle = self.wTree.get_widget(toggleName);
		stateName = action + "SuccessImage"
		self.image = self.wTree.get_widget(stateName);
		self.clear()
		self.label = self.toggle.get_label()

	# Clear the associated image
	def clear(self):
		self.image.set_from_file(None)

	# Get the label text
	def get_label(self):
		return self.label

	# Set the associated image to display success
	def success(self):
		self.image.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_BUTTON)

	# Set the associated image to display failure
	def fail(self):
		self.image.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_BUTTON)

	# Get the state of the associated CheckButton
	def get_state(self):
		return self.toggle.get_active()

	# Set the state of the associated CheckButton
	def set_state(self, state = True):
		self.toggle.set_active(state)

	# Set sensitivity of an action line
	def set_sensitive(self, sensitive = True):
		self.toggle.set_sensitive(sensitive)

	# Asynchronously run the action
	#	onEnd is a caller supplied callback that will be called
	#	when the action terminates.
	def run(self, onEnd):
		self.onEnd = onEnd
		self.clear()		# neither ok nor bad
		if self.get_state():
			self.executor = Executor(self.action,
						endCallback = self._end)
		else:
			self.onEnd(0)

	# Kill the action.
	def abort(self):
		self.executor.abort()

	# Helper method to evaluate the success of the action when it
	# ends. This updates the associated image, and then calls the
	# callback supplied at run time.
	def _end(self, state):
		if state == 0:
			self.success()
		else:
			self.fail()
		if (self.onEnd):
			self.onEnd(state)

class Sequence:
	"""This class handles the sequencing of actions.

	Handling a sequence of actions consists of:
		(a) Updating the GUI while checking constraints:
			toggled and check_constraints methods
		(b) Calling commands and threading from one to the next:
			run, stop, abort and _end methods
	"""

	# The followong defines all the actions that we know about and
	# their sequence.
	#
	# Note that the naming *must* to be consistent with the naming in
	# the GUI as we use string concatenation to generate the names of
	# widgets and callbacks associated with each action.
	actionNames = [
		"prepareIso", "unpackIso",
		"unpackRoot", "customizeRoot", "packRoot",
		"customizeIso",
		"unpackInitrd", "customizeInitrd", "packInitrd",
		"packIso",
		"test",
		"cleanup"
	]

	def __init__(self, wtree):
		self.wTree = wtree
		self.terminate = False
		self.currentAction = None
		self.currentIndex = -1
		self.already_checking = False
		self.shellRunning = False

		# Create the sequence of actions. Can only be done
		# dynamically here because we need to associated
		# the widgets in the tree passed in to the actions.
		# We also connect the toggle callbacks here, which
		# allows us to do consistency checking later.
		self.actions = []
		for aName in Sequence.actionNames:
			self.actions.append(Action(wtree, aName))
			signal = "on_" + aName + "CheckButton_toggled"
			self.wTree.signal_connect(signal, self.toggled)

		# Create list of buttons in interface
		self.buttons = [
			self.wTree.get_widget("runButton"),
			self.wTree.get_widget("configEditButton"),
			self.wTree.get_widget("prepareIsoEditButton"),
			self.wTree.get_widget("customizeRootEditButton"),
			self.wTree.get_widget("customizeIsoEditButton"),
			self.wTree.get_widget("customizeInitrdEditButton"),
			self.wTree.get_widget("customizeTestEditButton"),
			self.wTree.get_widget("shellButton"),
		]

		dic = {
			"on_shellButton_clicked" : self.shell,
		}
		self.wTree.signal_autoconnect(dic)

		self.shellButton = self.wTree.get_widget("shellButton")
		self.statusLabel = self.wTree.get_widget("statusLabel")

		# Enforce initial constraints
		self.check_constraints()

	# Method called when one of the action buttons is toggled
	def toggled(self, widget):
		self.check_constraints()

		# Toggeling off has no side effects.
		if not widget.get_active():
			return

		# Additional logic to activate toggles for actions that
		# can now be executed. Results in recursive calls to this
		# method, so make sure that there is no endless loop by
		# only ever toggeling actions that are further down the
		# sequence!
		next = None
		wTree = self.wTree
		if widget == wTree.get_widget("unpackIsoCheckButton"):
			#	unpackIso -> customizeIso
			next = wTree.get_widget("customizeIsoCheckButton")
		elif widget == wTree.get_widget("customizeIsoCheckButton"):
			#	customizeIso -> packIso
			next = wTree.get_widget("packIsoCheckButton")
		elif widget == wTree.get_widget("packIsoCheckButton"):
			#	packIso -> test
			next = wTree.get_widget("testCheckButton")
		elif widget == wTree.get_widget("unpackRootCheckButton"):
			#	unpackRoot -> customizeRoot
			next = wTree.get_widget("customizeRootCheckButton")
		elif widget == wTree.get_widget("customizeRootCheckButton"):
			#	customizeRoot -> packRoot
			next = wTree.get_widget("packRootCheckButton")
		elif widget == wTree.get_widget("packRootCheckButton"):
			#	packRoot -> customizeIso
			next = wTree.get_widget("customizeIsoCheckButton")
		elif widget == wTree.get_widget("unpackInitrdCheckButton"):
			#	unpackInitrd -> customizeInitrd
			next = wTree.get_widget("customizeInitrdCheckButton")
		elif widget == wTree.get_widget("customizeInitrdCheckButton"):
			#	customizeInitrd -> packInitrd
			next = wTree.get_widget("packInitrdCheckButton")
		elif widget == wTree.get_widget("packInitrdCheckButton"):
			#	packInitrd -> packIso
			next = wTree.get_widget("packIsoCheckButton")

		if next:
			next.set_active(True)

	# Method to check/enforce constraints
	#	This embodies logic like: you cannot customize the root
	#	if you have not ever unpacked it, a.s.o
	def check_constraints(self):
		# Prevent recursive check when toggles occur below
		if self.already_checking:
			return
		self.already_checking = True

		p = Project.get_instance()
		valid_project = p.valid_project()

		# Update status
		if not valid_project:
			self.status(_("No project"))
		else:
			self.status("")

		# Update button sensitivity
		for button in self.buttons:
			button.set_sensitive(valid_project)
		self.check_shellButton()

		# Only make those toggles sensitive that can be used now
		for index, aName in enumerate(Sequence.actionNames):
			if aName == "prepareIso":
				# - project defined
				if valid_project:
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "unpackIso":
				# - original iso file name known and
				# - project defined or
				# - prepareIso execute flag set
				if ((os.path.isfile(p.get_source()) and
				     valid_project) or
				    self.actions[index - 1].get_state()):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "unpackRoot":
				# - unpackIso selected
				# - unpacked Iso available
				# - no root shell running
				if ((self.actions[index - 1].get_state() or 
				     os.path.isdir(p.get_iso_dir())) and not
				    self.is_shellRunning()):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "customizeRoot":
				# - unpackRoot selected
				# - unpacked Root available
				# - no root shell running
				if ((self.actions[index - 1].get_state() or 
				     os.path.isdir(p.get_root_dir())) and not
				    self.is_shellRunning()):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "packRoot":
				# - unpackRoot selected
				# - unpacked Root available
				if (self.actions[index - 2].get_state() or
				    os.path.isdir(p.get_root_dir())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "customizeIso":
				# - unpackIso selected
				# - unpacked Iso available
				if (self.actions[index - 4].get_state() or 
				    os.path.isdir(p.get_iso_dir())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "unpackInitrd":
				# - unpackIso selected
				# - unpacked Iso available
				if (self.actions[index - 5].get_state() or
				    os.path.isdir(p.get_iso_dir())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "customizeInitrd":
				# - unpackInitrd selected
				# - unpacked Initrd available
				if (self.actions[index - 1].get_state() or
				    os.path.isdir(p.get_initrd_dir())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "packInitrd":
				# - unpackInitrd selected
				# - unpacked Initrd available
				if (self.actions[index - 2].get_state() or
				    os.path.isdir(p.get_initrd_dir())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "packIso":
				# - unpackIso selected
				# - unpacked Iso available
				if (self.actions[index - 8].get_state() or
				    os.path.isdir(p.get_iso_dir())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "test":
				# - packIso selected
				# - target ISO available
				if (self.actions[index - 1].get_state() or
				    os.path.isfile(p.get_target())):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			elif aName == "cleanup":
				# - project defined
				# - no root shell running
				if (valid_project and not
				    self.is_shellRunning()):
					self.actions[index].set_sensitive(True)
				else:
					self.actions[index].set_state(False)
					self.actions[index].set_sensitive(False)
			else:
				print "Unexpected step name"
		self.already_checking = False

	# Asyncronously start shell in root_fs
	def shell(self, widget):
		executor = Executor("shell", endCallback = self._shell_end)
		self.shellRunning = True
		self.check_constraints()

	# shellButton is only active if no sequence is running and rootfs
	#	unpacked and shell not already running, inactive otherwise
	def check_shellButton(self):
		p = Project.get_instance()
		if (p.valid_project() and
		    os.path.isdir(p.get_root_dir()) and
		    self.is_running() == False and
		    self.is_shellRunning() == False):
			self.shellButton.set_sensitive(True)
		else:
			self.shellButton.set_sensitive(False)

	def is_shellRunning(self):
		return self.shellRunning

	def _shell_end(self, status):
		self.shellRunning = False
		self.check_constraints()

	# Update the statusLabel
	def status(self, msg = ""):
		self.statusLabel.set_text(msg)

	# Run activated actions in sequence and update state.
	#	This method is also called from the _end method
	#	below to thread from one action to the next.
	def run(self, cont = False, onEnd = None, status = 0):
		self.onEnd = onEnd

		# Determine the next action to run
		if cont:				# Continue threading
			self.currentIndex += 1
		else:
			for action in self.actions:	# Clear old states
				action.clear()
			self.currentIndex = 0		# Start threading
			self.terminate = False		# No errors yet

		# Check for need to stop threading:
		#	- end of sequence reached
		#	- command exit status != 0
		#	- terminate flagged
		if (self.currentIndex >= len(self.actions) or
		    status != 0 or
		    self.terminate):
			self.status("")
			self.currentAction = None
			self.currentIndex = -1
			if (self.onEnd != None):
				self.onEnd(status)
			self.check_constraints()
			return

		# Change working directory to project directory
		os.chdir(Project.get_instance().get_project_dir())

		# Start the action (asynchronously)
		self.currentAction = self.actions[self.currentIndex]
		self.currentAction.run(self._end)

		# Update status
		self.check_constraints()
		if self.currentAction != None:
			label = self.currentAction.get_label()
			if label != None:
				self.status(label + "...")

	# Determine whether sequence is currently running
	def is_running(self):
		return self.currentAction != None

	# Called to stop execution of a sequence once the currently
	# running action has finished. It does *not* abort the currently
	# running action.
	def stop(self):
		self.terminate = True

	# Called to stop execution of a sequence aborting the currently
	# running action.
	def abort(self):
		if self.is_running():
			self.currentAction.abort()

	# Internal method: Called when an action terminates
	#	-> thread on to next
	def _end(self, status):
		self.run(True, self.onEnd, status)

# Create uckFlow GUI from the glade description and perform actions
class UckFlow:
	"""This is the UckFlow application"""

	def __init__(self, projectName = None):
		# Set the Glade file (found in module directory)
		self.dir = os.path.dirname(__file__)
		self.gladefile = os.path.join(self.dir, "uckFlow.glade")
		self.wTree = gtk.glade.XML(self.gladefile, "uckFlow") 
		self.projectName = self.wTree.get_widget("projectNameLabel")
		self.topLevel = self.wTree.get_widget("uckFlow");
		self.progressBar = self.wTree.get_widget("progressBar")
		self.config_time = 0
		self.logDialog = UckFlowLog(self.gladefile)
		self.logfile = None
		self.stdout = os.dup(sys.stdout.fileno())
		self.stderr = os.dup(sys.stderr.fileno())

		# Create dictionary of callbacks and autoconnect them
		dic = {
		"on_new_activate" : self.new,
		"on_new_from_template_activate" : self.new_from_template,
		"on_open_activate" : self.open,
		"on_quit_activate" : self.quit,
		"on_show_log_activate" : self.show_log,
		"on_about_activate" : self.about,
		"on_runButton_clicked" : self.run,
		"on_configEditButton_clicked" : self.config_edit,
		"on_prepareIsoEditButton_clicked" : self.prepare_iso_edit,
		"on_customizeRootEditButton_clicked" : self.customize_root_edit,
		"on_customizeIsoEditButton_clicked" : self.customize_iso_edit,
		"on_customizeInitrdEditButton_clicked" : self.customize_initrd_edit,
		"on_customizeTestEditButton_clicked" : self.customize_test_edit,
		"on_uckFlow_delete" : self.quit }
		self.wTree.signal_autoconnect(dic)

		# Initialize sequencing
		self.sequencer = Sequence(self.wTree)

		# Create preview widget for dialogs
		self.previewLabel = gtk.Label("PREVIEW");

		# Called with an argument? Otherwise start with builtin.
		if projectName:
			p = Project.get_instance()
			p.set_project_dir(projectName)

			# Get project configuration
			src = p.get_customize_dir()
			src = os.path.join(src, p.get("UCK_CONFIG"))
			self.config_read(src)
			self.redirect_io()
			msg = _("Opened project %s") % (p.get_project_name())
		else:
			msg = ""

		# Update from properties
		self.update_GUI(msg)

		# Periodically check for configuration file updates
		# gobject.idle_add(self.config_reread_if_changed)
		gobject.timeout_add(300, self.config_reread_if_changed)

	# Reset everything to a known state
	def reset(self):
		if self.sequencer.is_running():
			self.sequencer.abort()
		self.logDialog.hide()
		self.logDialog.set_logfile(None)
		Project.get_instance().reset()

	# Terminate the application
	def quit(self, widget = None, whatever = None):
		self.reset()
		gtk.main_quit()
		return False

	# Create a new project
	def new(self, widget, template = None):
		nTree = gtk.glade.XML(self.gladefile, "uckProjectNewDialog") 
		new = nTree.get_widget("uckProjectNewDialog")

		# Customize dialog to show what's going on
		label = gtk.Label(_("Select project to create"))
		new.set_extra_widget(label)
		new.set_preview_widget_active(False)

		response = new.run()

		if response == gtk.RESPONSE_OK:
			filename = new.get_filename()
			new.destroy()
			p = Project.get_instance()

			# Create well-known state
			self.reset()

			# Use template if specified
			if template != None:
				src = os.path.join(template, p.get("UCK_CONFIG"))
				self.config_read(src)

			# Remember new project directory
			p.set_project_dir(filename)

			# Pattern for all customization files
			target = p.get_customize_dir()
			src = p.get_template()
			files = os.path.join(src, "*")

			# Create/Use customization directory, and copy files
			if (not os.path.isdir(target) and
			    0 != os.system("mkdir " + target)):
				msg = _("Cannot create directory %s!") % (target)
				ErrorDialog(msg, self.topLevel)
			elif 0 != os.system("cp -r " + files + " " + target):
				msg = _("Cannot copy files to %s!") % (target)
				ErrorDialog(msg, self.topLevel)
			else:
				# Write current config to target
				target = os.path.join(target, p.get("UCK_CONFIG"))
				self.config_write(target)
			self.update_GUI(_("New project %s") % (p.get_project_name()))
		else:
			new.destroy()

	# Create a new project from an existing template
	def new_from_template(self, widget):
		nTree = gtk.glade.XML(self.gladefile, "uckProjectOpenDialog") 
		new = nTree.get_widget("uckProjectOpenDialog")
		path = Project.get_instance().get_template_dir()
		new.set_current_folder(path)

		# Customize dialog to show what's going on
		label = gtk.Label(_("Select template to use"))
		new.set_extra_widget(label)
		new.set_preview_widget(self.previewLabel)
		new.connect("update-preview", self.update_template_preview,
			self.previewLabel)
		new.set_preview_widget_active(False)

		response = new.run()
		if response == gtk.RESPONSE_OK:
			filename = new.get_filename()
			new.destroy()
			self.new(widget, filename)
		else:
			new.destroy()

	# Open an existing project
	def open(self, widget):
		oTree = gtk.glade.XML(self.gladefile, "uckProjectOpenDialog") 
		open = oTree.get_widget("uckProjectOpenDialog")

		# Customize dialog to show what's going on
		label = gtk.Label(_("Select project to open/create"))
		open.set_extra_widget(label)
		open.set_preview_widget(self.previewLabel)
		open.connect("update-preview", self.update_open_preview,
			self.previewLabel)
		open.set_preview_widget_active(False)

		response = open.run()

		if response == gtk.RESPONSE_OK:
			filename = open.get_filename()
			open.destroy()
			p = Project.get_instance()

			# Go to a well defined state
			self.reset()

			# Remember new project directory
			p.set_project_dir(filename)

			# Get project configuration
			src = p.get_customize_dir()
			src = os.path.join(src, p.get("UCK_CONFIG"))

			# Read project configuration
			self.config_read(src)

			# make sure project directory stays!
			p.set_project_dir(filename)

			# Redirect I/O to project log
			self.redirect_io()

			self.update_GUI(_("Opened project %s") % (p.get_project_name()))
		else:
			open.destroy()

	# Update template preview with project information
	def update_template_preview(self, file_chooser, label):
		p = Project.get_instance()
		filename = file_chooser.get_preview_filename()
		if filename != None:
			filename = os.path.join(filename, p.get("UCK_CONFIG"))
			if os.path.isfile(filename):
				info = Project.get_info(filename)
				info = "\n".join(info)
				label.set_text(_("UCK TEMPLATE:") + "\n" + info)
				file_chooser.set_preview_widget_active(True)
		else:
			file_chooser.set_preview_widget_active(False)

	# Update open preview with project information
	def update_open_preview(self, file_chooser, label):
		p = Project.get_instance()
		filename = file_chooser.get_preview_filename()
		if filename != None:
			filename = os.path.join(filename,
				p.get("UCK_CUSTOMIZE_DIR"),
				p.get("UCK_CONFIG"))
			if os.path.isfile(filename):
				info = Project.get_info(filename)
				info = "\n".join(info)
				label.set_text(_("UCK PROJECT:") + "\n" + info)
				file_chooser.set_preview_widget_active(True)
		else:
			file_chooser.set_preview_widget_active(False)

	# Update GUI with project information
	def update_GUI(self, message):
		p = Project.get_instance()
		self.sequencer.check_constraints()
		self.projectName.set_text(p.get_project_name() + "\n" +
			p.get_project_short())
		self.sequencer.status(message)

	# Show the log file window
	def show_log(self, widget):
		p = Project.get_instance()
		self.logDialog.set_logfile(p.get_logfile())
		self.logDialog.show()

	# Show the about information dialog
	def about(self, widget):
		aTree = gtk.glade.XML(self.gladefile, "uckFlowAboutDialog") 
		about = aTree.get_widget("uckFlowAboutDialog")
		about.run()
		about.destroy()

	# This is where all the work happens...
	#	The "Run" Button was clicked. This really is a kind of
	#	toggle: If we are not running we start to run, otherwise
	#	we stop.
	def run(self, widget):
		runButtonImage = self.wTree.get_widget("runButtonImage")
		runButtonLabel = self.wTree.get_widget("runButtonLabel")

		workImageFile = os.path.join(self.dir, "uck-working.gif")
		if self.sequencer.is_running():
			msg = _("Stopping...")
			runButtonLabel.set_label(msg)
			self.sequencer.status(msg)
			p = Project.get_instance()
			if p.get_terminate_behaviour() == Project.WAIT_STOP:
				self.sequencer.stop()
			else:
				self.sequencer.abort()
		else:
			# Latest possible point for changes to become effective
			self.config_reread_if_changed()
			runButtonImage.set_from_file(workImageFile)
			msg = _("Running...")
			runButtonLabel.set_label(msg)
			self.sequencer.status(msg)
			self.sequencer.run(onEnd = self.stop)

	# Method to toggle "Run" Button back to the original state when
	# the end od a sequence has been reached, either voluntarily or
	# unvoluntarily
	def stop(self, state):
		readyImageFile = os.path.join(self.dir, "uck-ready.gif")
		runButtonImage = self.wTree.get_widget("runButtonImage")
		runButtonLabel = self.wTree.get_widget("runButtonLabel")
		runButtonImage.set_from_file(readyImageFile);
		msg = _("Ready...")
		runButtonLabel.set_label(msg)
		self.sequencer.status(msg)

		if state != 0:
			msg = _("Customization failed with error %s") % (str(state))
			ErrorDialog(msg, self.topLevel)

	# Read a configuration file
	def config_read(self, src):
		p = Project.get_instance()
		try:
			f = file(src, 'r')
			p.read(f)
			f.close()
			self.config_time = os.stat(src)[ST_MTIME]
		except IOError, (errno, strerror):
			ErrorDialog("%s: %s" % (src, strerror))

	# Write a configuration file
	def config_write(self, dst):
		p = Project.get_instance()
		try:
			cfg = file(dst, 'w')
			p.write(cfg)
			cfg.close()
			self.config_time = os.stat(dst)[ST_MTIME]
			self.redirect_io()
		except IOError, (errno, strerror):
			ErrorDialog("%s: %s" % (dst, strerror))

	# Re-read project configuration and update GUI if config has changed
	#	As this is called from gobject it needs to return True.
	def config_reread_if_changed(self):
		cfg = Project.get_instance().get_project_config()
		if os.path.isfile(cfg):
			config_time = os.stat(cfg)[ST_MTIME]
			if config_time != self.config_time:
				self.config_read(cfg)
				self.redirect_io()
				self.update_GUI(_("Updated project"))
		return True

	# Redirect sys.stdout and sys.stderr to project logfile
	def redirect_io(self):
		p = Project.get_instance()

		lf = p.get_logfile()

		# Do nothing if logfile not changed
		if self.logfile == lf:
			return

		# Switch back to saved stdout/stderr
		if (lf == None or lf == ""):
			os.dup2(self.stdout, sys.stdout.fileno())
			os.dup2(self.stderr, sys.stderr.fileno())
			self.logfile = lf
			return

		# Switch to the named logfile
		try:
			print _("+++ Switching logfile to %s") % (lf)
			logfile = file(lf, "a")
			os.dup2(logfile.fileno(), sys.stdout.fileno())
			os.dup2(logfile.fileno(), sys.stderr.fileno())
			logfile.close()
			print _("+++ Logfile %s opened at %s") % (lf,
				strftime("%Y/%m/%d %H:%M:%S"))
			self.logfile = lf
		except IOError:
			pass

	# Asynchronously start editor editing project configuration data
	def config_edit(self, widget):
		p = Project.get_instance()
		editor = p.get_editor()
		cfgfile = p.get_project_config()
		os.system(editor + " \"" + cfgfile + "\" &")

	# Asynchronously start editor for prepare ISO script
	def prepare_iso_edit(self, widget):
		editor = Project.get_instance().get_editor()
		cfgfile = Project.get_instance().get_prepare_iso()
		os.system(editor + " \"" + cfgfile + "\" &")

	# Asynchronously start editor for root fs customization script
	def customize_root_edit(self, widget):
		editor = Project.get_instance().get_editor()
		cfgfile = Project.get_instance().get_customize_root()
		os.system(editor + " \"" + cfgfile + "\" &")

	# Asynchronously start editor for ISO customization script
	def customize_iso_edit(self, widget):
		editor = Project.get_instance().get_editor()
		cfgfile = Project.get_instance().get_customize_iso()
		os.system(editor + " \"" + cfgfile + "\" &")

	# Asynchronously start editor for INITRD customization script
	def customize_initrd_edit(self, widget):
		editor = Project.get_instance().get_editor()
		cfgfile = Project.get_instance().get_customize_initrd()
		os.system(editor + " \"" + cfgfile + "\" &")

	# Asynchronously start editor for test customization script
	def customize_test_edit(self, widget):
		editor = Project.get_instance().get_editor()
		cfgfile = Project.get_instance().get_customize_test()
		os.system(editor + " \"" + cfgfile + "\" &")
