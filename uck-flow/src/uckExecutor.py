# -*- coding: utf-8 -*-
#
# $Id$
#
# NAME:
#	uckExecutor -- execute commands
#
# DESCRIPTION:
#	Handle dispatch and asynchrounous execution of commands.
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
import subprocess
import gobject
import pygtk
pygtk.require("2.0")
import gtk

from uckProject import Project
import codecs

# message localization support
APP = "uckFlow"
DIR = "locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class Executor:
	"""This class maps actions to executable commands
	"""

	# Special commands (not in project configuration)
	sudo = "/usr/bin/gksudo"
	tail = "/usr/bin/tail -n +0 -f"
	kill = "/usr/bin/uck-killtree -l"
	shell = "/usr/bin/xterm -T"		# Lowest common denominator!

	def __init__(self, action, args = "", ioCallback = None, endCallback = None):
		self.ioCallback = ioCallback
		self.endCallback = endCallback
		self.proc = None
		self.runAs = False

		p = Project.get_instance()

		# Some shorthands
		p_dir = p.get_project_dir()
		p_src = p.get_source()
		p_iso = p.get_target()
		chroot = p.get_chroot_wrapper()
		unpack = p.get_unpack_iso()
		pack = p.get_pack_iso()
		p_desc = " --description \"" + p.get_project_name() + "\""

		# Special case: The customize root script runs within
		# a chroot environment so the path name is different!
		p_run = os.path.join("/tmp", p.get("UCK_CUSTOMIZE_DIR"),
				p.get("UCK_CUSTOMIZE_ROOT"))

		# self.executors maps symbolic command to
		#	[ real command, run as root?, print start/end msg ]
		self.executors = {
		"prepareIso" :	    [ p.get_prepare_iso() + " " + p_dir,
				      False, True ],
		"unpackIso" :	    [ unpack + " " + p_src + " " + p_dir,
				      True, True ],
		"unpackRoot" :	    [ p.get_unpack_root() + " " + p_dir,
				      True, True ],
		"customizeRoot" :   [ chroot + " " + p_dir + " " + p_run,
				      True, True ],
		"packRoot" :	    [ p.get_pack_root() + " " + p_dir,
				      True, True ],
		"customizeIso" :    [ p.get_customize_iso() + " " + p_dir,
				      True, True ],
		"unpackInitrd" :    [ p.get_unpack_initrd() + " " + p_dir,
				      True, True ],
		"customizeInitrd" : [ p.get_customize_initrd() + " " + p_dir,
				      True, True ],
		"packInitrd" :	    [ p.get_pack_initrd() + " " + p_dir,
				      True, True ],
		"packIso" :	    [ pack + " " + p_iso + " " + p_dir + p_desc,
				      True, True ],
		"test" :	    [ p.get_customize_test() + " " + p_dir,
				      False, True ],
		"cleanup" :	    [ p.get_cleanup() + " " + p_dir,
				      True, True ],
		"tail" :	    [ Executor.tail,
				      False, False ],
		"shell" :	    [ chroot +" "+ p_dir +" "+ Executor.shell +" \""+ p.get_project_name() + "\"",
				      True, True ],
		}

		# Flush any pending output
		while gtk.events_pending():
			gtk.main_iteration_do(False)

		# Evaluate need of chrooting and sudoing and create command
		self.command = self.executors[action][0]
		self.dolog = self.executors[action][2]
		if self.executors[action][1]:
			self.command = Executor.sudo + " -- " + self.command
			self.runAs = True

		# Create subprocess
		if ioCallback != None:
			self.proc = subprocess.Popen(self.command + " " + args,
				shell = True,
				preexec_fn = self.make_session,
				stdout = subprocess.PIPE,
				stderr = subprocess.STDOUT)

			# Add callback for input available from child
			gobject.io_add_watch(self.proc.stdout, gobject.IO_IN,
				self.io_callback)
		else:
			self.proc = subprocess.Popen(self.command + " " + args,
				shell = True,
				preexec_fn = self.make_session)

		if self.dolog:
			print _("+++ Started: %s") % (self.command + " " + args)

		# Add callback for child terminating
		gobject.child_watch_add(self.proc.pid, self.end_callback)

	# Create a session for the executed command. This is necessary to
	# be able to kill the whole process tree and not just the single
	# process that we initially started and know about.
	def make_session(self):
		os.setsid()

	# Kill the executor.
	#	This sends a SIGTERM to last child in the "session"
	def abort(self):
		if self.proc != None:
			if self.runAs:
				os.system("{0} -- {1} {2}".format(
					Executor.sudo, Executor.kill,
					self.proc.pid))
			else:
				os.system("{0} {1}".format(Executor.kill,
					self.proc.pid))

	# Called when the child has output to send
	def io_callback(self, fd, condition):
		if condition == gobject.IO_IN:
			# Cannot just read one byte reading utf-8!
			char = ''
			partial = ''
			while True:
				partial += fd.read(1)
				char, l = codecs.utf_8_decode(partial,
						'strict', 0)
				if char != '':
					break
			if self.ioCallback:
				self.ioCallback(char)
			return True		# Reregister callback
		else:
			return False		# Unregister callback

	# Called when the child terminates
	def end_callback(self, pid, state):
		if self.dolog:
			print _("+++ Ended with status %d: %s") % \
				(state, self.command)
		if self.endCallback:
			self.endCallback(state)
		self.proc = None

	# Get PID of running process
	def pid(self):
		return self.proc.pid

	# Get state of running process
	def state(self):
		return self.proc.returncode
