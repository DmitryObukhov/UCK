#!/usr/bin/env python
# -*- coding: utf_8 -*-
#
# $Id$
#
# NAME:
#	setup.py -- uck-flow distribution script
#
# SYNOPSIS:
#	python setup.py install
#
# DESCRIPTION:
#
# COPYRIGHT:
#	Copyright © 2010, The UCK Team
#
# LICENSE:
#	uck-flow is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	uck-flow is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with uck-flow.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
from distutils.core import setup

# Dynamically determine VERSION from file
p = os.popen("cat VERSION")
if p == 0:
	print >>sys.stderr, "Cannot find VERSION file!"
	sys.exit(2)
else:
	v = p.read().strip()
	p.close()

setup(	name = 'uckflow',
	version = v,
	description = 'The uck-flow GUI for the Ubuntu Customization Toolkit',
	author = 'Wolf Geldmacher',
	author_email = 'wolf <at> womaro.ch',
	license = 'GPL',
	long_description = 'uck-flow is a python/glade/GTK GUI for UCK (the Ubuntu Customization Kit) that alleviates the creation of Ubuntu customizations by providing a workflow.',
	url = 'http://uck.sourceforge.net',
	scripts = [ 'uck-flow', 'uck-killtree' ],
	packages = [ 'uckflow' ],
	package_dir = {
		'uckflow' : 'src'
	},
	package_data = {
		'uckflow' :  [
			'uckFlow.glade',
			'uckFlow.gladep',
			'uck-full.gif',
			'uck-ready.gif',
			'uck-working.gif'
		      ]
	},
	data_files = [
		(
		'/usr/lib/uck/templates/default', [
			'templates/default/project.uck',
			'templates/default/prepare_iso',
			'templates/default/customize_root',
			'templates/default/finalize_root',
			'templates/default/customize_initrd',
			'templates/default/customize_iso',
			'templates/default/customize_test',
		 ],
		),
		(
		'/usr/lib/uck/templates/updated', [
			'templates/updated/project.uck',
			'templates/updated/customize_iso',
			'templates/updated/prepare_iso',
			'templates/updated/customize_root',
			'templates/updated/finalize_root',
			'templates/updated/customize_initrd',
			'templates/updated/customize_test',
		 ],
		),
		(
		'/usr/lib/uck/templates/localized', [
			'templates/localized/project.uck',
			'templates/localized/customize_iso',
			'templates/localized/prepare_iso',
			'templates/localized/customize_root',
			'templates/localized/finalize_root',
			'templates/localized/customize_initrd',
			'templates/localized/customize_test',
		 ],
		),
		(
		'/usr/lib/uck/templates/interactive', [
			'templates/interactive/project.uck',
			'templates/interactive/customize_iso',
			'templates/interactive/prepare_iso',
			'templates/interactive/customize_root',
			'templates/interactive/finalize_root',
			'templates/interactive/customize_initrd',
			'templates/interactive/customize_test',
			'templates/interactive/gui.sh',
		 ],
		),
		(
		'/usr/share/locale-langpack/de/LC_MESSAGES', [
			'locale/de/LC_MESSAGES/uckFlow.mo',
		 ],
		),
		(
		'/usr/share/applications', [
			'uck-flow.desktop',
		 ],
		),
		(
		'/usr/share/man/man1', [
			'doc/uck-flow.1',
		 ],
		),
	],
)

# Use:
#	python setup.py sdist		to create a source distribution
