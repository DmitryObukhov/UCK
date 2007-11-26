#!/bin/bash

###################################################################################
# UCK - Ubuntu Customization Kit                                                  #
# Copyright (C) 2006-2007 UCK Team                                                #
#                                                                                 #
# This program is free software; you can redistribute it and/or                   #
# modify it under the terms of the GNU General Public License                     #
# as published by the Free Software Foundation; version 2                         #
# of the License.                                                                 #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program; if not, write to the Free Software                     #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA. #
###################################################################################

function check_if_user_is_root()
{
	if [ $UID != 0 ]; then
		echo "You need root privileges"
		exit 2
	fi
}

function unmount_directory()
{
	DIR_TO_UNMOUNT="$1"
	if mountpoint -q "$DIR_TO_UNMOUNT"; then
		echo "Unmounting directory $DIR_TO_UNMOUNT..."
		umount -l "$DIR_TO_UNMOUNT" || failure "Cannot unmount directory $DIR_TO_UNMOUNT, error=$?"
	fi
}

function unmount_pseudofilesystems()
{
	if [ -n "$REMASTER_DIR" ]; then
		for i in "$REMASTER_DIR/tmp/.X11-unix" "$REMASTER_DIR"/lib/modules/*/volatile "$REMASTER_DIR"/proc "$REMASTER_DIR"/sys "$REMASTER_DIR"/dev/pts; do
			unmount_directory "$i"
		done
	fi
}

function unmount_loopfilesystems()
{
	if [ -n "$SQUASHFS_MOUNT_DIR" ]; then
		unmount_directory "$SQUASHFS_MOUNT_DIR"
	fi

	if [ -n "$ISO_MOUNT_DIR" ]; then
		unmount_directory "$ISO_MOUNT_DIR"
	fi
}

function unmount_all()
{
	unmount_pseudofilesystems
	unmount_loopfilesystems
}

function failure()
{
	unmount_all
	echo "$@"
	exit 2
}

function script_cancelled_by_user()
{
	failure "Script cancelled by user"
}

function remove_directory()
{
	DIR_TO_REMOVE="$1"
	if [ "$DIR_TO_REMOVE" = "/" ]; then
		failure "Trying to remove root directory"
	fi
	rm -rf "$DIR_TO_REMOVE"
}

function unpack_initrd()
{
	remove_remaster_initrd
	mkdir -p "$INITRD_REMASTER_DIR" || failure "Cannot create directory $INITRD_REMASTER_DIR"

	echo "Unpacking initrd image..."
	pushd "$INITRD_REMASTER_DIR" || failure "Failed to change directory to $INITRD_REMASTER_DIR, error=$?"

	if [ -e "$ISO_REMASTER_DIR/casper/initrd.gz" ]; then
		INITRD_FILE="$ISO_REMASTER_DIR/casper/initrd.gz"
	elif [ -e "$ISO_REMASTER_DIR/install/initrd.gz" ]; then
		INITRD_FILE="$ISO_REMASTER_DIR/install/initrd.gz"
	else
		failure "Can't find initrd.gz file"
	fi

	cat "$INITRD_FILE" | gzip -d | cpio -i
	RESULT=$?
	if [ $RESULT -ne 0 ]; then
		failure "Failed to unpack $INITRD_FILE to $INITRD_REMASTER_DIR, error=$RESULT"
	fi

	popd
}

function pack_initrd()
{
	if [ ! -e "$INITRD_REMASTER_DIR" ]; then
		failure "Initrd remastering directory does not exists"
	fi

	echo "Packing initrd image..."
	pushd "$INITRD_REMASTER_DIR" || failure "Failed to change directory to $INITRD_REMASTER_DIR, error=$?"
	find | cpio -H newc -o | gzip >"$REMASTER_HOME/initrd.gz"
	RESULT=$?
	if [ $RESULT -ne 0 ]; then
		rm "$REMASTER_HOME/initrd.gz"
		failure "Failed to compress initird image $INITRD_REMASTER_DIR to $REMASTER_HOME/initrd.gz, error=$RESULT"
	fi
	popd

	if [ -e "$ISO_REMASTER_DIR/casper" ]; then
		INITRD_FILE="$ISO_REMASTER_DIR/casper/initrd.gz"
	elif [ -e "$ISO_REMASTER_DIR/install" ]; then
		INITRD_FILE="$ISO_REMASTER_DIR/install/initrd.gz"
	else
		failure "Can't find where to copy the initrd.gz file"
	fi

	mv "$REMASTER_HOME/initrd.gz" "$INITRD_FILE" || failure "Failed to move $NEW_FILES_DIR/initrd.gz to $INITRD_FILE, error=$?"
}

function mount_iso()
{
	echo "Mounting ISO image..."
	mkdir -p "$ISO_MOUNT_DIR" || failure "Cannot create directory $ISO_MOUNT_DIR, error=$?"
	mount "$ISO_IMAGE" "$ISO_MOUNT_DIR" -o loop || failure "Cannot mount $ISO_IMAGE in $ISO_MOUNT_DIR, error=$?"
}

function unmount_iso()
{
	if [ -e "$ISO_MOUNT_DIR" ] ; then
		echo "Unmounting ISO image..."
		umount "$ISO_MOUNT_DIR" || echo "Failed to unmount ISO mount directory $ISO_MOUNT_DIR, error=$?"
		rmdir "$ISO_MOUNT_DIR" || echo "Failed to remove ISO mount directory $ISO_MOUNT_DIR, error=$?"
	fi
}

function unpack_iso()
{
	echo "Unpacking ISO image..."
	cp -a "$ISO_MOUNT_DIR" "$ISO_REMASTER_DIR" || failure "Failed to unpack ISO from $ISO_MOUNT_DIR to $ISO_REMASTER_DIR"
	
	#can't trap errors with diff because of its return codes,
	#we pass the diff's output to cut cause we strip the version number
	if [ -e "$ISO_REMASTER_DIR/casper/filesystem.manifest" ]; then
		diff --unchanged-group-format='' "$ISO_REMASTER_DIR/casper/filesystem.manifest" "$ISO_REMASTER_DIR/casper/filesystem.manifest-desktop" | cut -d ' ' -f 1 > "$ISO_REMASTER_DIR/casper/manifest.diff"
	fi
}

function mount_squashfs()
{
	echo "Mounting SquashFS image..."
	mkdir -p "$SQUASHFS_MOUNT_DIR" || failure "Cannot create directory $SQUASHFS_MOUNT_DIR, error=$?"
	mount -t squashfs "$SQUASHFS_IMAGE" "$SQUASHFS_MOUNT_DIR" -o loop || failure "Cannot mount $SQUASHFS_IMAGE in $SQUASHFS_MOUNT_DIR, error=$?"
}

function unmount_squashfs()
{
	if [ -e "$SQUASHFS_MOUNT_DIR" ] ; then
		echo "Unmounting SquashFS image..."
		umount "$SQUASHFS_MOUNT_DIR" || echo "Failed to unmount SquashFS mount directory $SQUASHFS_MOUNT_DIR, error=$?"
		rmdir "$SQUASHFS_MOUNT_DIR" || echo "Failed to remove SquashFS mount directory $SQUASHFS_MOUNT_DIR, error=$?"
	fi
}

function unpack_rootfs()
{
	echo "Unpacking SquashFS image..."
	cp -a "$SQUASHFS_MOUNT_DIR" "$REMASTER_DIR" || failure "Cannot copy files from $SQUASHFS_MOUNT_DIR to $REMASTER_DIR, error=$?"
}

function prepare_rootfs_for_chroot()
{
	if [ ! -e "$REMASTER_DIR" ]; then
		failure "Remastering root directory does not exists"
	fi

	mount -t proc proc "$REMASTER_DIR/proc" || echo "Failed to mount $REMASTER_DIR/proc, error=$?"
	mount -t sysfs sysfs "$REMASTER_DIR/sys" || echo "Failed to mount $REMASTER_DIR/sys, error=$?"
	mount -t devpts none "$REMASTER_DIR/dev/pts" || failure "Failed to mount $REMASTER_DIR/dev/pts, error=$?"

	#create backup of root directory
	chroot "$REMASTER_DIR" cp -a /root /root.saved || failure "Failed to create backup of /root directory, error=$?"

	if [ -e $REMASTER_HOME/customization-scripts ]; then
		echo "Copying customization scripts..."
		cp -a "$REMASTER_HOME/customization-scripts" "$REMASTER_DIR/tmp" || failure "Cannot copy files from $CUSTOMIZE_DIR to $REMASTER_CUSTOMIZE_DIR, error=$?"
	fi

	echo "Copying resolv.conf..."
	cp -f /etc/resolv.conf "$REMASTER_DIR/etc/resolv.conf" || failure "Failed to copy resolv.conf to image directory, error=$?"

	echo "Copying local apt cache, if available"
	if [ -e "$APT_CACHE_SAVE_DIR" ]; then
		mv "$REMASTER_DIR/var/cache/apt/" "$REMASTER_DIR/var/cache/apt.original" || failure "Cannot move $REMASTER_DIR/var/cache/apt/ to $REMASTER_DIR/var/cache/apt.original, error=$?"
		mv "$APT_CACHE_SAVE_DIR" "$REMASTER_DIR/var/cache/apt" || failure "Cannot copy apt cache dir $APT_CACHE_SAVE_DIR to $REMASTER_DIR/var/cache/apt/, error=$?"
	else
		cp -a "$REMASTER_DIR/var/cache/apt/" "$REMASTER_DIR/var/cache/apt.original" || failure "Cannot copy $REMASTER_DIR/var/cache/apt/ to $REMASTER_DIR/var/cache/apt.original, error=$?"
	fi

	echo "Mounting X11 sockets directory to allow access from customization environment..."
	mkdir -p "$REMASTER_DIR/tmp/.X11-unix" || failure "Cannot create mount directory $REMASTER_DIR/tmp/.X11-unix, error=$?"
	mount --bind /tmp/.X11-unix "$REMASTER_DIR/tmp/.X11-unix" || failure "Cannot bind mount /tmp/.X11-unix in  $REMASTER_DIR/tmp/.X11-unix, error=$?"

	if [ -e "$REMASTER_HOME/customization-scripts/Xcookie" ] ; then
		echo "Creating user directory..."
		UCK_USER_HOME_DIR=`xauth info|grep 'Authority file'| sed "s/[ \t]//g" | sed "s/\/\.Xauthority//" | cut -d ':' -f2`
		chroot "$REMASTER_DIR" mkdir -p "$UCK_USER_HOME_DIR" || failure "Cannot create user directory, error=$?"

		echo "Copying X authorization file to chroot filesystem..."
		cat "$REMASTER_HOME/customization-scripts/Xcookie" | chroot "$REMASTER_DIR" xauth -f /root/.Xauthority merge - || failure "Failed to merge X authorization file, error=$?"
		cat "$REMASTER_HOME/customization-scripts/Xcookie" | chroot "$REMASTER_DIR" xauth merge - || failure "Failed to merge X authorization file in user directory, error=$?"
	fi
}

function chroot_rootfs()
{
	chroot "$REMASTER_DIR" "$WHAT_TO_EXTECUTE"
}

function clean_rootfs_after_chroot()
{
	unmount_pseudofilesystems
	save_apt_cache

	echo "Cleaning up apt"
	chroot "$REMASTER_DIR" apt-get clean || failure "Failed to run apt-get clean, error=$?"

	echo "Removing customize dir..."
	#Run in chroot to be on safe side
	chroot "$REMASTER_DIR" rm -rf "$REMASTER_CUSTOMIZE_RELATIVE_DIR" || failure "Cannot remove customize dir $REMASTER_CUSTOMIZE_RELATIVE_DIR, error=$?"

	echo "Cleaning up temporary directories..."
	#Run in chroot to be on safe side
	chroot "$REMASTER_DIR" rm -rf '/tmp/*' '/tmp/.*' '/var/tmp/*' '/var/tmp/.*' #2>/dev/null

	echo "Restoring /root directory..."
	chroot "$REMASTER_DIR" rm -rf /root || failure "Cannot remove /root directory, error=$?"
	chroot "$REMASTER_DIR" mv /root.saved /root

	echo "Removing /home/username directory, if created..."
	UCK_USER_HOME_DIR=`xauth info|grep 'Authority file'| sed "s/[ \t]//g" | sed "s/\/\.Xauthority//" | cut -d ':' -f2`
	chroot "$REMASTER_DIR" rm -rf "$UCK_USER_HOME_DIR" # 2>/dev/null

	echo "Restoring resolv.conf..."
	rm -f "$REMASTER_DIR/etc/resolv.conf" || failure "Failed to remove resolv.conf, error=$?"
}

function save_apt_cache()
{
	echo "Saving apt cache"
	if [ -e "$APT_CACHE_SAVE_DIR" ]; then
		mv -f "$APT_CACHE_SAVE_DIR" "$APT_CACHE_SAVE_DIR.old" || failure "Cannot save old apt-cache $APT_CACHE_SAVE_DIR to $APT_CACHE_SAVE_DIR.old, error=$?"
	fi
	mv "$REMASTER_DIR/var/cache/apt/" "$APT_CACHE_SAVE_DIR" || failure "Cannot move current apt-cache $REMASTER_DIR/var/cache/apt/ to $APT_CACHE_SAVE_DIR, error=$?"
	mv "$REMASTER_DIR/var/cache/apt.original" "$REMASTER_DIR/var/cache/apt" || failure "Cannot restore original apt-cache $REMASTER_DIR/var/cache/apt.original to $REMASTER_DIR/var/cache/apt, error=$?"
}

function prepare_new_files_directories()
{
	echo "Preparing directory for new files"
	if [ -e "$NEW_FILES_DIR" ]; then
		remove_directory "$NEW_FILES_DIR" || failure "Failed to remove directory $NEW_FILES_DIR"
	fi
	mkdir -p "$NEW_FILES_DIR"
}

function pack_rootfs()
{
	if [ -e "$REMASTER_DIR" ]; then
		echo "Updating files lists..."
		chroot "$REMASTER_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$ISO_REMASTER_DIR/casper/filesystem.manifest" || failure "Cannot update filesystem.manifest, error=$?"
		if [ $CLEAN_DESKTOP_MANIFEST == 1 ] && [ -e "$ISO_REMASTER_DIR/casper/manifest.diff" ]; then
			#stripping version number from manifest 
			cat "$ISO_REMASTER_DIR/casper/filesystem.manifest" | cut -d ' ' -f 1 > "$ISO_REMASTER_DIR/filesystem.manifest.tmp"
			# can't trap errors with diff because of its return codes
			diff --unchanged-group-format='' "$ISO_REMASTER_DIR/filesystem.manifest.tmp" "$ISO_REMASTER_DIR/casper/manifest.diff" > "$ISO_REMASTER_DIR/filesystem.manifest-desktop.tmp"
			#building the right manifest-desktop file
			chroot "$REMASTER_DIR"  dpkg-query -W --showformat='${Package} ${Version}\n' `cat "$ISO_REMASTER_DIR/filesystem.manifest-desktop.tmp"` | egrep '.+ .+' > "$ISO_REMASTER_DIR/casper/filesystem.manifest-desktop"
			#removing temp files
			rm "$ISO_REMASTER_DIR/filesystem.manifest.tmp" "$ISO_REMASTER_DIR/filesystem.manifest-desktop.tmp"
		else
			cp "$ISO_REMASTER_DIR/casper/filesystem.manifest" "$ISO_REMASTER_DIR/casper/filesystem.manifest-desktop" || failure "Failed to copy $ISO_REMASTER_DIR/casper/filesystem.manifest to $ISO_REMASTER_DIR/casper/filesystem.manifest-desktop"
		fi

		echo "Packing SquashFS image..."
		if [ -e "$ISO_REMASTER_DIR/casper/filesystem.squashfs" ]; then
			rm -f "$ISO_REMASTER_DIR/casper/filesystem.squashfs" || failure "Cannot remove $ISO_REMASTER_DIR/casper/filesystem.squashfs to make room for created squashfs image, error=$?"
		fi

		EXTRA_OPTS=""

		if [ -e "$CUSTOMIZE_DIR/rootfs.sort" ] ; then
			#FIXME: space not allowed in $CUSTOMIZE_DIR
			EXTRA_OPTS="-sort $CUSTOMIZE_DIR/rootfs.sort"
		fi

		mksquashfs "$REMASTER_DIR" "$ISO_REMASTER_DIR/casper/filesystem.squashfs" $EXTRA_OPTS || failure "Failed to create squashfs image to $ISO_REMASTER_DIR/casper/filesystem.squashfs, error=$?"
	else
		echo "Remastering root directory does not exists"
	fi
}

function remove_iso_remaster_dir()
{
	if [ -e "$ISO_REMASTER_DIR" ] ; then
		echo "Removing ISO remastering dir..."
		remove_directory "$ISO_REMASTER_DIR" || failure "Failed to remove directory $ISO_REMASTER_DIR, error=$?"
	fi
}

function remove_remaster_dir()
{
	if [ -e "$REMASTER_DIR" ] ; then
		echo "Removing remastering root dir..."
		remove_directory "$REMASTER_DIR"
	fi
}

function remove_remaster_initrd()
{
	if [ -e  "$INITRD_REMASTER_DIR" ]; then
		echo "Removing initrd remastering dir..."
		remove_directory "$INITRD_REMASTER_DIR"
	fi
}

function update_iso_locale()
{
	echo "Updating locale"

	if [ -e "$CUSTOMIZE_DIR/livecd_locale" ]; then
		LIVECD_LOCALE=`cat "$CUSTOMIZE_DIR/livecd_locale"`
		cat "$ISO_REMASTER_DIR/isolinux/isolinux.cfg" | sed "s#\<append\>#append debian-installer/locale=$LIVECD_LOCALE#g" >"$NEW_FILES_DIR/isolinux.cfg"
		RESULT=$?
		if [ $RESULT -ne 0 ]; then
			failure "Failed to filter $ISO_REMASTER_DIR/isolinux/isolinux.cfg into $NEW_FILES_DIR/isolinux.cfg, error=$RESULT"
		fi

		cp -a "$NEW_FILES_DIR/isolinux.cfg" "$ISO_REMASTER_DIR/isolinux/isolinux.cfg" || failure "Failed to copy $NEW_FILES_DIR/isolinux.cfg to $ISO_REMASTER_DIR/isolinux/isolinux.cfg, error=$?"
	fi
}

function pack_iso()
{
	if [ ! -e "$ISO_REMASTER_DIR" ]; then
		failure "ISO remastering directory does not exists"
	fi

	#skip boot.cat, isolinux.bin, md5sums.txt
	#mismatches are for those files, because they are generated by mkisofs or by generating MD5 sums:
	EXCLUDED_FROM_MD5="./isolinux/isolinux.bin ./isolinux/boot.cat ./md5sum.txt ./manifest.diff"
	EXCLUDED_FROM_MD5_EXPRESSION=$(echo $EXCLUDED_FROM_MD5 | tr ' ' '|')
	EXCLUDED_FROM_MD5_EXPRESSION="($EXCLUDED_FROM_MD5_EXPRESSION)"

	echo "Updating md5sums..."
	pushd "$ISO_REMASTER_DIR"
	find . -type f -print0 | grep --null-data -v -E "$EXCLUDED_FROM_MD5_EXPRESSION" | xargs -0 md5sum > md5sum.txt
	popd

	echo "Packing ISO image..."

	LIVECD_ISO_DESCRIPTION="Remastered Ubuntu LiveCD"

	if [ -e "$CUSTOMIZE_DIR/iso_description" ] ; then
		LIVECD_ISO_DESCRIPTION=`cat "$CUSTOMIZE_DIR/iso_description"`
	fi

	echo "ISO description set to: $LIVECD_ISO_DESCRIPTION"

	MKISOFS_EXTRA_OPTIONS=""
	if [ -e "$CUSTOMIZE_DIR/mkisofs_extra_options" ] ; then
		MKISOFS_EXTRA_OPTIONS=`cat "$CUSTOMIZE_DIR/mkisofs_extra_options"`
	fi

	if [ "$1" = "ppc" ]; then
		mkisofs -o "$NEW_FILES_DIR/$NEW_ISO_FILE_NAME" \
			-p "Ubuntu Customization Kit - http://uck.sf.net" \
			-probe -map "$UCK_LIBRARIES_DIR/hfs.map" -chrp-boot -iso-level 2 \
			-part -no-desktop -r --netatalk -hfs \
			-hfs-bless "$ISO_REMASTER_DIR/install" \
			-x "$ISO_REMASTER_DIR"/casper/manifest.diff \
			-V "$LIVECD_ISO_DESCRIPTION" \
			$MKISOFS_EXTRA_OPTIONS \
			"$ISO_REMASTER_DIR"
	elif [ "$1" = "x86_64" ]; then
		mkisofs -o "$NEW_FILES_DIR/$NEW_ISO_FILE_NAME" \
			-b "isolinux/isolinux.bin" -c "isolinux/boot.cat" \
			-p "Ubuntu Customization Kit - http://uck.sf.net" \
			-no-emul-boot -V "$LIVECD_ISO_DESCRIPTION" -r -J -l \
			-x "$ISO_REMASTER_DIR"/casper/manifest.diff \
			$MKISOFS_EXTRA_OPTIONS \
			"$ISO_REMASTER_DIR"
	elif [ "$1" = "ia64" ]; then
		mkisofs -o "$NEW_FILES_DIR/$NEW_ISO_FILE_NAME" \
		-b "isolinux/isolinux.bin" -c "isolinux/boot.cat" \
		-no-emul-boot -V "$LIVECD_ISO_DESCRIPTION" -J -r \
		-x "$ISO_REMASTER_DIR"/casper/manifest.diff \
		$MKISOFS_EXTRA_OPTIONS \
		"$ISO_REMASTER_DIR"
	else
		mkisofs -o "$NEW_FILES_DIR/$NEW_ISO_FILE_NAME" \
			-b "isolinux/isolinux.bin" -c "isolinux/boot.cat" \
			-p "Ubuntu Customization Kit - http://uck.sf.net" \
			-no-emul-boot -boot-load-size 4 -boot-info-table \
			-V "$LIVECD_ISO_DESCRIPTION" -cache-inodes -r -J -l \
			-x "$ISO_REMASTER_DIR"/casper/manifest.diff \
			$MKISOFS_EXTRA_OPTIONS \
			"$ISO_REMASTER_DIR"
	fi

	RESULT=$?
	if [ $RESULT -ne 0 ]; then
		failure "Failed to pack ISO image, error=$RESULT"
	fi
}

function generate_md5_for_new_iso()
{
	echo "Generating md5sum for newly created ISO..."
	cd $NEW_FILES_DIR
	md5sum $NEW_ISO_FILE_NAME > $NEW_ISO_FILE_NAME.md5
}

######################
# some useful things #
######################

if [ -e libraries/remaster-live-cd.sh ]; then
	UCK_LIBRARIES_DIR=./libraries
else
	UCK_LIBRARIES_DIR=/usr/lib/uck/
fi

export LC_ALL=C
check_if_user_is_root
trap unmount_all EXIT
trap script_cancelled_by_user SIGINT