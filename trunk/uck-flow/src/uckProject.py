# -*- coding: utf-8 -*-
#
# $Id$
#
# NAME:
#	uckProject -- class to handle all configuration for an uckFlow
#
# DESCRIPTION:
#	The main class defined in this file is the single point of focus
#	for all configuration information needed by uckFlow. A project
#	is implemented as a singleton for ease of use.
#
#	The magic incantation is:
#		from uckProject import Project
#		...
#		project = Project.get_instance()
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
import re

from uckDialogs import ErrorDialog
from StringIO import StringIO
from Singleton import Singleton
from StaticMethod import StaticMethod

# message localization support
APP = "uckFlow"
DIR = "locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

defaultConfiguration = """
#
# $Id$
#
# This is an uckFlow project configuration, same as is found in the template
# files:
# - Comments (optionally) precede simple VARIABLE=VALUE lines
# - Variable names consist of characters in the set [A-Za-y_0-9]
# - Variable values can be in single or double quotes and cannot (yet) contain
#   single or double quotes themselves.
# - Variable values cannot b continued over the end of a line
# - No variable substitution is done, ever.
# - You can add almost arbitrary additional variables to a project.
UCK_CONFIG_VERSION="1.0"

# The UCK_EDITOR variable defines the (absolute path name to) the (graphical)
# editor that should be invoked to edit all customization scripts.
UCK_EDITOR="/usr/bin/gedit"

# This variable defines the name of the project and will also be used
# when the final ISO imageis created
UCK_PROJECT_NAME="Generic Ubuntu Remix"

# This variable has a very short description of the project
UCK_PROJECT_SHORT='Generic Ubuntu Customization'

# The UCK_PROJECT_DIR Variable defines the directory where all the work will
# happen. You will need enough disk space available at that location. This
# configuration parameter accepts directories in the shell ~ notation.
UCK_PROJECT_DIR="~/tmp"

# The UCK_TEMPLATE variable has the name of the currently used template. This
# matches to a subdirectory name in UCK_TEMPLATE_DIR.
UCK_TEMPLATE="default"

# The UCK_TERMINATE_BEHAVIOUR determines the way customization is aborted when
# the Run/Stop toggle is pressed in the GUI: If set to "force", the currently
# running action will forcibly be terminated - possibly leaving the system in
# an inconsistent state. If set to "wait" the currently running action will
# be allowed to end in its time and only then will no further activity occur.
UCK_TERMINATE_BEHAVIOUR="wait"

# The UCK_SOURCE parameter can either contain the absolute pathname to the
# source of the ISO image to customize or a file name relative to the
# UCK_PROJECT_DIR. Typical values are "source.iso", iff you want to start with
# an ISO image in the project directory or "/dev/sr0" if you want to start
# by ripping the CD in the first optical drive.
UCK_SOURCE="source.iso"

# The UCK_TARGET parameter can either contain the absolute pathname of the
# ISO image to create or a file name relative to the UCK_PROJECT_DIR.
# Typical value is "target.iso"
UCK_TARGET="target.iso"

# UCK_LOGFILE is the file name (absolute path or relative to UCK_PROJECT_DIR)
# that will contain the log of all activities in the project. An empty name
# means that whatever logfile was used before (usually stdout) should continue
# to be used.
UCK_LOGFILE=""

# UCK_PREPARE_ISO is the name of a script (absolute path or relative to
# UCK_PROJECT_DIR/customization-scripts) that can be run before customization
# proper starts. This is where you could pull  a current ISO of Ubuntu from
# some repository or rip an image form CD.
UCK_PREPARE_ISO="prepare_iso"

# UCK_CUSTOMIZE_ROOT is the name of a script (relative (and *only* relative!)
# to UCK_PROJECT_DIR/customization-scripts) that will be run from within the
# unpacked root file system. This is where packages can be
# installed/updated/removed.
UCK_CUSTOMIZE_ROOT="customize_root"

# UCK_CUSTOMIZE_ISO is the name of a script (absolute path or relative to
# UCK_PROJECT_DIR/customization-scripts) that is run to customize the ISO
# file system outside of the root or initrd area. It is commonly used to
# copy a new kernel/initrd after having updated those in the root file
# system to where they can be accessed on the CD or to add files that
# should be accessible in operating systems other than Ubuntu or to remove
# unwanted files from the source dsitribution.
UCK_CUSTOMIZE_ISO="customize_iso"

# UCK_CUSTOMIZE_INITRD is the name of a script (absolute path or relative to
# UCK_PROJECT_DIR/customization-scripts) used to customize the INITRD of the
# Ubuntu live system.
UCK_CUSTOMIZE_INITRD="customize_initrd"

# UCK_CUSTOMIZE_TEST is the name of a script (absolute path or relative to
# UCK_PROJECT_DIR/customization-scripts) used to test the generated UCK_TARGET
# (or to deliver it to another server, burn it to a CD/DVD and similar tasks.
UCK_CUSTOMIZE_TEST="customize_test"

# UCK_BINDIR designates the directory where all the binaries supplied with
# UCK have been installed. Note that changing this variable usually only makes
# sense for the UCK/uckFlow maintainers.
UCK_BINDIR="/usr/bin"

# The template directory has subdirectories for each template provided by UCK.
# Within a template directory there will be one subdirectory (usually
# named "customization-scripts" - but see CUSTOMIZE_DIR in this file) which
# contains the templates project definitions (UCK_TEMPLATE.uck) and the scripts
# that will be copied to UCK_PROJECT_DIR/customization-scripts to create an
# initial configuration.
UCK_TEMPLATE_DIR="/usr/lib/uck/templates"
"""

# The following configuration is built-in and takes precedence
# over any user configuration. They can neither be edited nor overridden.
builtinConfiguration = {
	"UCK_CUSTOMIZE_DIR"	: "customization-scripts",
	"UCK_CONFIG"		: "project.uck",
	"UCK_UNPACK_ISO"	: "uck-remaster-unpack-iso",
	"UCK_ISO_DIR"		: "remaster-iso",
	"UCK_UNPACK_ROOT"	: "uck-remaster-unpack-rootfs",
	"UCK_ROOT_DIR"		: "remaster-root",
	"UCK_CHROOT_WRAPPER"	: "uck-remaster-chroot-rootfs",
	"UCK_PACK_ROOT"		: "uck-remaster-pack-rootfs",
	"UCK_UNPACK_INITRD"	: "uck-remaster-unpack-initrd",
	"UCK_PACK_INITRD"	: "uck-remaster-pack-initrd",
	"UCK_INITRD_DIR"	: "remaster-initrd",
	"UCK_PACK_ISO"		: "uck-remaster-pack-iso",
	"UCK_FINALIZE"		: "uck-remaster-umount",
	"UCK_NEW_DIR"		: "remaster-new-files",
	"UCK_CLEAN"		: "uck-remaster-clean-all",
}

class CfgObject:
	"""An object as found in a project configuration file.
	"""

	# The following attributes are for the sake of the uckParamEditor:
	READ_ONLY	= 0x01
	NO_DELETE	= 0x02

	builtinAttrs = {
		"UCK_EDITOR"		: NO_DELETE,
		"UCK_CONFIG_VERSION"	: NO_DELETE|READ_ONLY,
		"UCK_PROJECT_NAME"	: NO_DELETE,
		"UCK_PROJECT_SHORT"	: NO_DELETE,
		"UCK_PROJECT_DIR"	: NO_DELETE|READ_ONLY,
		"UCK_TERMINATE_BEHAVIOUR" : NO_DELETE,
		"UCK_SOURCE"		: NO_DELETE,
		"UCK_TARGET"		: NO_DELETE,
		"UCK_LOGFILE"		: NO_DELETE,
		"UCK_BINDIR"		: NO_DELETE|READ_ONLY,
		"UCK_TEMPLATE_DIR"	: NO_DELETE|READ_ONLY,
	}

	# Constructor
	def __init__(self, name, value, comment, project, attrs = 0):
		self.name = name
		self.value = value
		self.comment = comment
		self.order = 0

		# Ignore and set predefined attributes for some built-ins:
		if name in CfgObject.builtinAttrs:
			self.attrs = CfgObject.builtinAttrs[name]
		else:
			self.attrs = attrs

		# New configuration parameters get added at the end
		if project != None and name not in project:
			self.order = len(project.keys())
			project[name] = self

	def get_name(self):
		return self.name

	def get_comment(self):
		return self.comment

	def get_value(self):
		return self.value

	def set_value(self, value = ""):
		self.value = value

	def set_comment(self, comment = ""):
		self.comment = comment

	def is_readonly(self):
		if self.attrs & CfgObject.READ_ONLY:
			return True
		return False

	def can_be_deleted(self):
		if self.attrs & CfgObject.NO_DELETE:
			return False
		return True

	def get_order(self):
		return self.order

	# Write an configuration object to a stream
	def write(self, stream = sys.stdout):
		for line in self.comment.splitlines():
			stream.write("# " + line + "\n")
		stream.write(self.name + "='" + self.value + "'\n\n")

class Project(Singleton):
	"""This class, together with CfgObject above, handles all the
	configuration for the uckFlow environment.
	"""

	# Project termination behaviour:
	FORCE_STOP = "force"	# Kill any process step running
	WAIT_STOP = "wait"	# Wait for current step to end and then stop

	# Two regular expressions used to parse configuration data
	comment = re.compile(r'#\s*(?P<text>.*)')
	nvpair = re.compile(r'(?P<name>[A-Za-z_0-9]+)=["\']?(?P<value>[^\'"]*|\\\'*)["\']?.*')

	# Static method to access the single instance. cf. Singleton
	# and StaticMethod
	_instance = None
	def get_instance():
		if Project._instance == None:
			Project._instance = Project()
		return Project._instance
	get_instance = StaticMethod(get_instance)

	# Static method to read project information from a stream
	def config_read(stream, project):
		n, v, c = None, "", ""

		for line in stream.readlines():
			# Strip leading and trailing white space
			line = line.strip()

			# Perform match on comment and name/value pair
			comment = Project.comment.match(line)
			nvpair = Project.nvpair.match(line)

			# Analyze result of match
			if comment != None:
				c += comment.group('text') + "\n"
			elif nvpair != None:
				n = nvpair.group('name')
				v = nvpair.group('value')
				CfgObject(n, v, c, project)
				n, v, c = None, "", ""
			else:
				pass		# Silently ignore trash
	config_read = StaticMethod(config_read)

	# Determine if a project is a valid uckFlow project
	def valid_project(self):
		return (os.path.isdir(self.get_project_dir()) and
			os.path.isdir(self.get_customize_dir()) and
			os.path.isfile(self.get_project_config()))

	# Get UCK_PROJECT_NAME and UCK_PROJECT_SHORT from a config file
	#	Returns list with to items (name and short description)
	def get_info(name):
		project = {}

		try:
			f = file(name, "r")
			Project.config_read(f, project)
			f.close()
		except IOError, (errno, strerror):
			ErrorDialog("%s: %s" % (name, strerror))
			return [ "", "" ]

		result = []
		for name in [ 'UCK_PROJECT_NAME', 'UCK_PROJECT_SHORT' ]:
			if name in project:
				result.append(project[name].get_value())
			else:
				result.append("")
		return result
	get_info = StaticMethod(get_info)

	# Constructor
	def __init__(self):
		# Guard against the constructor being called more than once:
		#	Essentially all access should be through get_instance
		#	above, but if somebody should call Project() we should
		#	still react sensibly. Sensibly here means that we
		#	print a message but do not perform first time
		#	initialization. Other possible strategies would be
		#	throwing an exception or deleting the constructor
		#	after first use as outlined below.
		if Project._instance != None:
			print "Singleton constructor called more than once!"
			return
		Project._instance = self

		# Read default configuration from built-in string
		self.reset()

		# Set default value for useMount
		self.set_use_mount(False)

		# As an alternative to the guard technique above we could
		# just delete this constructor after first use by doing:
		#del Project.__init__

	# Read default configuration from built-in string
	def reset(self):
		self.project = {}
		stream = StringIO(defaultConfiguration)
		Project.config_read(stream, self.project)
		stream.close()

	# Write configuration information to a stream.
	#	Two pass to preserve original ordering
	def write(self, stream = sys.stdout):
		vars = []
		for cfgo in self.project.values():
			vars.insert(cfgo.get_order(), cfgo)
		for cfgo in vars:
			cfgo.write(stream)

	# Read configuration information from a stream (file or StringIO)
	def read(self, stream):
		self.project = {}
		Project.config_read(stream, self.project)

	# Get value of a configuration variable
	def get(self, name):
		# Builtin names take precedence...
		if name in builtinConfiguration:
			return builtinConfiguration[name]

		# ... over project/user defined names
		if name in self.project:
			value = self.project[name].get_value()
		else:
			value = ""
		return value

	# Set the value of a configuration variable
	def set(self, name, value, comment = ""):
		if name in builtinConfiguration:
			print _("Warning: Cannot override builtin %s") % (name)
		elif name in self.project:
			self.project[name].set_value(value)
		else:
			CfgObject(name, value, comment, self.project)

	# Set usemount property
	def set_use_mount(self, value = False):
		self.useMount = value

	# Get usemount property
	def get_use_mount(self):
		return self.useMount

	# Get rel/abs path of editor to use
	def get_editor(self):
		return self.get("UCK_EDITOR")

	# Get name of config file
	def get_config(self):
		return self.get("UCK_CONFIG")

	# Get name of project
	def get_project_name(self):
		return self.get("UCK_PROJECT_NAME")

	# Get project short description
	def get_project_short(self):
		return self.get("UCK_PROJECT_SHORT")

	# Get path to binaries
	def get_bin_dir(self):
		return self.get("UCK_BINDIR")

	# Get path to source ISO file
	def get_source(self):
		return self.p_path("UCK_SOURCE")

	# Get project terminate behaviour
	def get_terminate_behaviour(self):
		return self.get("UCK_TERMINATE_BEHAVIOUR")

	# Create path relative to project directory or return absolute path
	# for an configuration item.
	def p_path(self, name):
		path = self.get(name)
		if os.path.isabs(path):
			return path
		else:
			return os.path.join(self.get_project_dir(), path)

	# Create path relative to project directory or return absolute path
	# for an configuration item.
	def c_path(self, name):
		path = self.get(name)
		if os.path.isabs(path):
			return path
		else:
			return os.path.join(self.get_customize_dir(), path)

	# Create path relative to binaries directory or return absolute path
	# for an configuration item.
	def b_path(self, name):
		path = self.get(name)
		if os.path.isabs(path):
			return path
		else:
			return os.path.join(self.get_bin_dir(), path)

	# Get path of template dir
	def get_template_dir(self):
		return self.get("UCK_TEMPLATE_DIR")

	# Get path to a template
	#	Templates are directories that contain customization scripts
	#	and a config.
	def get_template(self):
		return os.path.join(self.get_template_dir(),
			self.get("UCK_TEMPLATE"))

	# Get path to template project config file
	def get_template_config(self):
		return os.path.join(self.get_template(), self.get_config())

	# Get path to project directory
	#	This expands the ~/ notation
	def get_project_dir(self):
		return os.path.expanduser(self.get("UCK_PROJECT_DIR"))

	# Set path to project directory
	def set_project_dir(self, path):
		self.set("UCK_PROJECT_DIR", path)

	# Get path to project script and config directory
	def get_customize_dir(self):
		return self.p_path("UCK_CUSTOMIZE_DIR")

	# Get path to project configuration file
	def get_project_config(self):
		return os.path.join(self.get_customize_dir(), self.get_config())

	# Get path to prepare ISO script
	def get_prepare_iso(self):
		return self.c_path("UCK_PREPARE_ISO")
		
	# Get path to rootfs directory
	def get_root_dir(self):
		return self.p_path("UCK_ROOT_DIR")

	# Get path to initrd directory
	def get_initrd_dir(self):
		return self.p_path("UCK_INITRD_DIR")

	# Get path to ISO directory
	def get_iso_dir(self):
		return self.p_path("UCK_ISO_DIR")

	# Get path to unpack ISO command
	def get_unpack_iso(self):
		return self.b_path("UCK_UNPACK_ISO")

	# Get path to unpack rootfs command
	def get_unpack_root(self):
		return self.b_path("UCK_UNPACK_ROOT")

	# Get path to rootfs customization script
	def get_customize_root(self):
		return self.c_path("UCK_CUSTOMIZE_ROOT")

	# Get path to pack rootfs command
	def get_pack_root(self):
		return self.b_path("UCK_PACK_ROOT")

	# Get path to ISO customization script
	def get_customize_iso(self):
		return self.c_path("UCK_CUSTOMIZE_ISO")

	# Get path to unpack INITRD command
	def get_unpack_initrd(self):
		return self.b_path("UCK_UNPACK_INITRD")

	# Get path to customize INITRD script
	def get_customize_initrd(self):
		return self.c_path("UCK_CUSTOMIZE_INITRD")

	# Get path to pack INITRD command
	def get_pack_initrd(self):
		return self.b_path("UCK_PACK_INITRD")

	# Get path to pack ISO command
	def get_pack_iso(self):
		return self.b_path("UCK_PACK_ISO")

	# Get path to finalize command
	def get_finalize(self):
		return self.b_path("UCK_FINALIZE")

	# Get path to test script
	def get_customize_test(self):
		return self.c_path("UCK_CUSTOMIZE_TEST")

	# Get path to cleanup command
	def get_cleanup(self):
		return self.b_path("UCK_CLEAN")

	# Get path to target ISO file
	def get_target(self):
		return self.p_path("UCK_TARGET")

	# Get path to log file
	def get_logfile(self):
		if self.get("UCK_LOGFILE") != "":
			return self.p_path("UCK_LOGFILE")
		else:
			return ""

	# Get path to chroot wrapper
	def get_chroot_wrapper(self):
		return self.b_path("UCK_CHROOT_WRAPPER")

	# Get path to directory containg the new files
	def get_new_dir(self):
		return self.p_path("UCK_NEW_DIR")
