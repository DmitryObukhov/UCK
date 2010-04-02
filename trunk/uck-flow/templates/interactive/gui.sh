#!/bin/bash
#
# $Id: gui.sh,v 2.1 2010-02-22 09:19:04 wjg Exp $
#
# NAME:
#	gui.sh -- library of gui functions
#
# SYNOPSIS:
#	. gui.sh
#
# DESCRIPTION:
#	This module encapsulates the different dialogs (Gnome, KDE, command
#	line) and provides a uniform interface to the first available one.
#
#	The order dialogs are searched for is:
#		If within an X session:
#			kdialog
#			Xdialog
#			(zenity - currently broken?)
#		If not found or not in an X session:
#			dialog
#
#	The following functions are provided by this library:
#		find_dialog
#			called internally to determine the dialog
#			package to use
#		dialog_menu "description" "item1" ["item2" ...]
#			Offer a menu and return item selected
#		dialog_multi_choice "description" "item1" ["item2" ...]
#			Offer a menu and return list of items selected
#		dialog_line_input "description" ["default input"]
#			get a single line of input and return that single line
#		dialog_choose_file "title"
#			Offer a file selection dialog for the current directory
#			and return the file selected
#		dialog_msgbox "title" "message"
#			Create a message box and display a message
#		dialog_question "title" "question"
#			Create a question dialog and return the answer
#
#	The following functions are required to be defined by this library:
#		failure "message"
#			A function that displays a failure message and
#			terminates processing (via exit)
#
# COPYRIGHT:
#	Copyright © 2006-2010, The UCK Team
#
# LICENSE:
#	UCK is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	UCK is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with UCK.  If not, see <http://www.gnu.org/licenses/>.

function find_dialog()
{
	if [ ! -z "$DISPLAY" ] ; then
		DIALOG=`which kdialog`

		if [ ! -z "$DIALOG" ]; then
			DIALOG_TYPE=kdialog
		else
			DIALOG=`which Xdialog`

			if [ ! -z "$DIALOG" ]; then
				DIALOG_TYPE=dialog
			fi
		fi

		if [ -z "$DIALOG" ]; then
			DIALOG=`which zenity`

			if [ ! -z "$DIALOG" ]; then
				DIALOG_TYPE=zenity
			fi
		fi
	fi

	if [ -z "$DIALOG" ]; then
		DIALOG=`which dialog`

		if [ ! -z "$DIALOG" ]; then
			DIALOG_TYPE=dialog
		fi
	fi

	if [ -z $DIALOG ]; then
		failure "You need kdialog, Xdialog, dialog or zenity application to run this script, please install it using 'apt-get install packagename' where packagename is 'kdebase-bin' for kdialog, 'xdialog' for dialog, 'dialog' for dialog. If you are using text-mode, you need to install dialog."
	fi
}

function dialog_menu()
{
	DESCRIPTION="$1"
	shift

	declare -a PARAMS

	if [ "$DIALOG_TYPE" = "zenity" ]; then
		declare -i i=0
		for v; do
			PARAMS[$i]="$v"
			i+=1
		done
		$DIALOG --list --text "$DESCRIPTION" --column "" "${PARAMS[@]}" --width=500 --height=400
	else
		if [ "$DIALOG_TYPE" = "kdialog" ] ; then
			declare -i i=0
			for v; do
				PARAMS[$i]="$v"
				i+=1
				PARAMS[$i]="$v" #yes, 2 times as kdialog requires key and value
				i+=1
			done
			$DIALOG --menu "$DESCRIPTION" "${PARAMS[@]}"
		else
			declare -i i=0
			for v; do
				PARAMS[$i]="$v"
				i+=1
				PARAMS[$i]="Language"
				i+=1
			done
			$DIALOG --stdout --menu "$DESCRIPTION" 20 30 10 "${PARAMS[@]}"
		fi
	fi
}

function dialog_multi_choice()
{
	DESCRIPTION="$1"
	shift

	if [ "$DIALOG_TYPE" = "zenity" ]; then
		for i; do
			PARAMS="$PARAMS $i $i"
		done
		$DIALOG --separator $'\n' --list --checklist --multiple --text "$DESCRIPTION" --column "" --column ""  $PARAMS --width=500 --height=400
	else
		if [ "$DIALOG_TYPE" = "kdialog" ] ; then
			for i; do
				PARAMS="$PARAMS $i $i 0"
			done
			$DIALOG --separate-output --checklist "$DESCRIPTION" $PARAMS
		else
			for i; do
				PARAMS="$PARAMS $i Language 0"
			done
			$DIALOG --stdout --separate-output --checklist "$DESCRIPTION" 20 30 10 $PARAMS
		fi
	fi

	RESULT=$?
	return $RESULT
}

function dialog_line_input()
{
	DESCRIPTION="$1"
	INITIAL_VALUE="$2"

	if [ "$DIALOG_TYPE" = "zenity" ] ; then
		$DIALOG --entry --text "$DESCRIPTION" --entry-text "$INITIAL_VALUE"
	else
		if [ "$DIALOG_TYPE" = "kdialog" ] ; then
			$DIALOG --inputbox "$DESCRIPTION" "$INITIAL_VALUE"
		else
			$DIALOG --stdout --inputbox "$DESCRIPTION" 20 30 "$INITIAL_VALUE"
		fi
	fi

	RESULT=$?
	return $RESULT
}

function dialog_choose_file()
{
	TITLE="$1"

	if [ "$DIALOG_TYPE" = "zenity" ] ; then
		$DIALOG --title "$TITLE" --file-selection "`pwd`/"
	else
		if [ "$DIALOG_TYPE" = "kdialog" ] ; then
			$DIALOG --title "$TITLE" --getopenfilename "`pwd`/"
		else
			$DIALOG --stdout --title "$TITLE" --fselect "`pwd`/" 10 70
		fi
	fi
}

function dialog_msgbox()
{
	TITLE="$1"
	TEXT="$2"

	if [ "$DIALOG_TYPE" = "zenity" ]; then
		echo -n "$TEXT" | $DIALOG --title "$TITLE" --text-info --width=500 --height=400
	else
		$DIALOG --title "$TITLE" --msgbox "$TEXT" 20 80
	fi
}

function dialog_question()
{
	TITLE="$1"
	TEXT="$2"

	if [ "$DIALOG_TYPE" = "zenity" ]; then
		$DIALOG --title "$TITLE" --question --text "$TEXT"
	else
		$DIALOG --title "$TITLE" --yesno "$TEXT" 20 80
	fi
}

find_dialog
