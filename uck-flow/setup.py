#!/usr/bin/env python
# -*- coding: utf_8 -*-
#
# $Id: setup.py,v 2.7 2010-04-02 05:48:56 wjg Exp $
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
from distutils.core import setup

setup(	name = 'UckFlow',
	version = '0.3',
	description = 'The uck-flow GUI for the Ubuntu Customization Toolkit',
	author = 'Wolf Geldmacher',
	author_email = 'wolf <at> womaro.ch',
	license = 'GPL',
	long_description = 'uck-flow is a python/glade/GTK GUI based on UCK (the Ubuntu Customization Kit) that alleviates the creation of Ubuntu customizations by providing a workflow.',
	url = 'http://uck.sourceforge.net',
	scripts = [ 'uck-flow', 'killtree' ],
	packages = [ 'UckFlow' ],
	package_dir = {
		'UckFlow' : 'src'
	},
	package_data = {
		'UckFlow' :  [
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
	],
)

# Use:
#	python setup.py sdist		to create a source distribution
