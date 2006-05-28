#!/bin/bash

ISO_IMAGE="$1"
CUSTOMIZE_DIR="$2"
ISO_MOUNT_DIR=~/tmp/iso-source2
SQUASHFS_IMAGE="$ISO_MOUNT_DIR/casper/filesystem.squashfs"
SQUASHFS_MOUNT_DIR=~/tmp/squashfs-source
REMASTER_DIR=~/tmp/remaster-root
REMASTER_CUSTOMIZE_RELATIVE_DIR="tmp/customize-dir"
REMASTER_CUSTOMIZE_DIR="$REMASTER_DIR/$REMASTER_CUSTOMIZE_RELATIVE_DIR"
CUSTOMIZATION_SCRIPT="$REMASTER_CUSTOMIZE_RELATIVE_DIR/customize"
#Name of directory where packages downloaded by apt are kept across build runs
#Allows saving bandwidth for downloading all updates
#Important: no "/" at the end of directory name!
APT_CACHE_SAVE_DIR=~/tmp/remaster-apt-cache
NEW_FILES_DIR=~/tmp/remaster-new-files
LIVECD_ISO_DESCRIPTION="Remastered LiveCD"

echo "Starting CD remastering on " `date`
echo "Cutomization dir=$CUSTOMIZE_DIR" 

function usage()
{
	echo "Usage: $0 path-to-iso-file.iso customization-dir/"
}

function failure()
{
	echo "$@"
	exit 2
}

function removeDirectory()
{
	DIR_TO_REMOVE="$1"
	if [ "$DIR_TO_REMOVE" = "/" ]; then
		failure "Trying to remove root directory"
	fi
	rm -rf "$DIR_TO_REMOVE"
}

function unpack_initrd()
{
	#not ready yet
	failure "Not implemented"
	cat $1 | cpio -i 
}

function pack_initrd()
{
	#not ready yet
	failure "Not implemented"
	find | cpio -H newc -o | gzip >initrd.gz
}

function mount_iso()
{
	echo "Mounting ISO image..."
	mkdir -p "$ISO_MOUNT_DIR" || failure "Cannot create directory $ISO_MOUNT_DIR, error=$?"
	mount "$ISO_IMAGE" "$ISO_MOUNT_DIR" -o loop || failure "Cannot mount $ISO_IMAGE in $ISO_MOUNT_DIR, error=$?"
}

function unpack_squashfs()
{
	echo "Mounting SquashFS image..."
	
	mkdir -p "$SQUASHFS_MOUNT_DIR" || failure "Cannot create directory $SQUASHFS_MOUNT_DIR, error=$?"
	mount -t squashfs "$SQUASHFS_IMAGE" "$SQUASHFS_MOUNT_DIR" -o loop || failure "Cannot mount $SQUASHFS_IMAGE in $SQUASHFS_MOUNT_DIR, error=$?"
	
	if [ -e "$REMASTER_DIR" ]; then
		echo "Remaster root directory $REMASTER_DIR already exists, aborting. "
		echo "If it doesn't contain valuable data, remove it and restart the script "
		exit 3
	fi
	
	echo "Copying data to remastering root directory..."
	cp -a "$SQUASHFS_MOUNT_DIR" "$REMASTER_DIR" || failure "Cannot copy files from $SQUASHFS_MOUNT_DIR to $REMASTER_DIR, error=$?"
}

function prepare_rootfs_for_net_update()
{
	echo "Copying resolv.conf"
	cp -f /etc/resolv.conf "$REMASTER_DIR/etc/resolv.conf" || failure "Failed to copy resolv.conf to image directory, error=$?"
	
	echo "Copying local apt cache, if available"
	if [ -e "$APT_CACHE_SAVE_DIR" ]; then
		mv "$REMASTER_DIR/var/cache/apt/" "$REMASTER_DIR/var/cache/apt.original" || failure "Cannot move $REMASTER_DIR/var/cache/apt/ to $REMASTER_DIR/var/cache/apt.original, error=$?"
		mv "$APT_CACHE_SAVE_DIR" "$REMASTER_DIR/var/cache/apt" || failure "Cannot copy apt cache dir $APT_CACHE_SAVE_DIR to $REMASTER_DIR/var/cache/apt/, error=$?"
	else
		cp -a "$REMASTER_DIR/var/cache/apt/" "$REMASTER_DIR/var/cache/apt.original" || failure "Cannot copy $REMASTER_DIR/var/cache/apt/ to $REMASTER_DIR/var/cache/apt.original, error=$?"
	fi
}

function run_rootfs_chroot_customization()
{
	echo "Copying customization files..."
	cp -a "$CUSTOMIZE_DIR" "$REMASTER_CUSTOMIZE_DIR" || failure "Cannot copy files from $CUSTOMIZE_DIR to $REMASTER_CUSTOMIZE_DIR, error=$?"
	
	echo "Running customization script..."
	chroot "$REMASTER_DIR" "/$CUSTOMIZATION_SCRIPT" || failure "Running customization script failed, error=$?"
	echo "Customization script finished"
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

function clean_rootfs()
{
	echo "Cleaning up apt"
	chroot "$REMASTER_DIR" apt-get clean || failure "Failed to run apt-get clean, error=$?"
	
	echo "Removing customize dir"
	#Run in chroot to be on safe side
	chroot "$REMASTER_DIR" rm -rf "$REMASTER_CUSTOMIZE_RELATIVE_DIR" || failure "Cannot remove customize dir $REMASTER_CUSTOMIZE_RELATIVE_DIR, error=$?"
	
	echo "Cleaning up temporary directories"
	#Run in chroot to be on safe side
	chroot "$REMASTER_DIR" 'rm -rf /tmp/* /tmp/.* /var/tmp/* /var/tmp/.*' || echo "Warning: Cannot remove temoporary files, error=$?. Ignoring"
	
	#mv -f "$RESOLV_CONF_BACKUP" "$REMASTER_DIR/etc/resolv.conf" || failure "Failed to restore resolv.conf, error=$?"
	rm -f "$REMASTER_DIR/etc/resolv.conf" || failure "Failed to remove resolv.conf, error=$?"
}

function prepare_new_files_directories()
{
	echo "Preparing directory for new files"
	if [ -e "$NEW_FILES_DIR" ]; then
		if [ "$NEW_FILES_DIR"  = "/" ]; then
			failure "Trying to remove root!"
		fi
		removeDirectory "$NEW_FILES_DIR" || failure "Failed to remove directory $NEW_FILES_DIR"
	fi
	mkdir -p "$NEW_FILES_DIR"
}

function pack_rootfs()
{
	echo "Updating files lists"
	chroot "$REMASTER_DIR" dpkg-query -W --showformat='${Package} ${Version}\n' > "$NEW_FILES_DIR/filesystem.manifest" || failure "Cannot update filesystem.manifest, error=$?"
	cp "$NEW_FILES_DIR/filesystem.manifest" "$NEW_FILES_DIR/filesystem.manifest-desktop" || failure "Failed to copy $NEW_FILES_DIR/filesystem.manifest to $NEW_FILES_DIR/filesystem.manifest-desktop"
	
	echo "Preparing SquashFS image"
	mksquashfs "$REMASTER_DIR" "$NEW_FILES_DIR/filesystem.squashfs" || failure "Failed to create squashfs image to NEW_FILES_DIR/filesystem.squashfs, error=$?"
	
	echo "Removing remastering root dir"
	
	removeDirectory "$REMASTER_DIR"
}

function update_iso_locale()
{
	echo "Updating locale"
	
	if [ -e "$CUSTOMIZE_DIR/livecd_locale" ]; then
		LIVECD_LOCALE=`cat "$CUSTOMIZE_DIR/livecd_locale"`
		cat "$ISO_MOUNT_DIR/isolinux/isolinux.cfg" | sed "s#\<append\>#append debian-installer/locale=$LIVECD_LOCALE#g" >"$NEW_FILES_DIR/isolinux.cfg"
		RESULT=$?
		if [ $RESULT -ne 0 ]; then
			failure "Failed to filter $ISO_MOUNT_DIR/isolinux/isolinux.cfg into $NEW_FILES_DIR/isolinux.cfg, error=$RESULT"
		fi
	else
		cat "$ISO_MOUNT_DIR/isolinux/isolinux.cfg" >"$NEW_FILES_DIR/isolinux.cfg"
		RESULT=$?
		if [ $RESULT -ne 0 ]; then
			failure "Failed to copy $ISO_MOUNT_DIR/isolinux/isolinux.cfg into $NEW_FILES_DIR/isolinux.cfg, error=$RESULT"
		fi
	fi
}

function pack_isofs()
{
	echo "Updating md5sums"
	UPDATED_FILES="./casper/filesystem.manifest ./casper/filesystem.manifest-desktop ./casper/filesystem.squashfs"
	pushd "$ISO_MOUNT_DIR"
	find . -type f -print | while read CURRENT_FILE; do
		FOUND=0
		for UPDATED_FILE in $UPDATED_FILES; do
			if [ "$UPDATED_FILE" = "$CURRENT_FILE" ]; then
				MODIFIED_FILE=`basename "$UPDATED_FILE"`
				SUM=`md5sum "$NEW_FILES_DIR/$MODIFIED_FILE"`
				RESULT=$?
				if [ $RESULT -ne 0 ]; then
					failure "Failed to compute md5sum for $NEW_FILES_DIR/$MODIFIED_FILE, error=$RESULT "
				fi
				SUM=`echo $SUM | cut -d' ' -f1`
				echo "$SUM  $UPDATED_FILE" >>"$NEW_FILES_DIR/md5sum.txt"
				
				FOUND=1
			fi
		done
		if [ "$FOUND" -eq 0 ]; then
			md5sum "$CURRENT_FILE" >>"$NEW_FILES_DIR/md5sum.txt"
		fi
	done
	popd
	
	echo "Creating ISO image"    
	
	cp -a "$ISO_MOUNT_DIR/isolinux/isolinux.bin" "$NEW_FILES_DIR/" || failure "Error copying isolinux.bin, error=$?"
	#cp -a "$ISO_MOUNT_DIR/isolinux/pl.tr" "$NEW_FILES_DIR/en.tr" || failure "Error copying pl.tr to en.tr, error=$?"
	
	REPLACED_PATHS="-x $ISO_MOUNT_DIR/casper/filesystem.squashfs -x $ISO_MOUNT_DIR/casper/filesystem.manifest -x $ISO_MOUNT_DIR/casper/filesystem.manifest-desktop"
	CHANGED_PATHS="casper/filesystem.squashfs=$NEW_FILES_DIR/filesystem.squashfs casper/filesystem.manifest=$NEW_FILES_DIR/filesystem.manifest  casper/filesystem.manifest-desktop=$NEW_FILES_DIR/filesystem.manifest-desktop"
	REPLACED_PATHS="$REPLACED_PATHS -x $ISO_MOUNT_DIR/isolinux/isolinux.bin -x $ISO_MOUNT_DIR/isolinux/boot.cat"
	CHANGED_PATHS="$CHANGED_PATHS isolinux/isolinux.bin=$NEW_FILES_DIR/isolinux.bin"
	#REPLACED_PATHS="$REPLACED_PATHS -x $ISO_MOUNT_DIR/isolinux/en.tr "
	#CHANGED_PATHS="$CHANGED_PATHS isolinux/en.tr=$NEW_FILES_DIR/en.tr"
	REPLACED_PATHS="$REPLACED_PATHS -x $ISO_MOUNT_DIR/casper/initrd.gz "
	CHANGED_PATHS="$CHANGED_PATHS casper/initrd.gz=$NEW_FILES_DIR/initrd.gz"
	
	mkisofs -o "$NEW_FILES_DIR/livecd.iso" \
		-b "isolinux/isolinux.bin" -c "isolinux/boot.cat" \
		-no-emul-boot -boot-load-size 4 -boot-info-table \
		-V "$LIVECD_ISO_DESCRIPTION" -cache-inodes -r -J -l \
		$REPLACED_PATHS \
		-graft-points $CHANGED_PATHS \
		"$ISO_MOUNT_DIR"
	RESULT=$?
	if [ $RESULT -ne 0 ]; then
		failure "Failed to create ISO image, error=$RESULT"
	fi
}

if [ -z "$ISO_IMAGE" ]; then
	usage
	exit 1
fi

if [ -z "$CUSTOMIZE_DIR" ]; then
	usage
	exit 1
fi

if true; then #KLDEBUG, KLSKIP 

mount_iso
unpack_squashfs
prepare_rootfs_for_net_update
run_rootfs_chroot_customization

echo "Pausing for manual customization, press Enter when finished..."
read DUMMY

fi #KLSKIP

save_apt_cache
clean_rootfs
prepare_new_files_directories
pack_rootfs

update_iso_locale

pack_isofs

umount "$SQUASHFS_MOUNT_DIR" || echo "Failed to unmount SQUASHFS mount directory $SQUASHFS_MOUNT_DIR, error=$?"
rmdir "$SQUASHFS_MOUNT_DIR" || echo "Failed to remove SQUASHFS mount directory $SQUASHFS_MOUNT_DIR, error=$?"

umount "$ISO_MOUNT_DIR" || echo "Failed to unmount ISO mount directory $ISO_MOUNT_DIR, error=$?"
rmdir "$ISO_MOUNT_DIR" || echo "Failed to remove ISO mount directory $ISO_MOUNT_DIR, error=$?"
