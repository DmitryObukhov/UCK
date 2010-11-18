#!/bin/bash
#
# Script to build a local version of the package
#
VERSION=`cat VERSION`
SUITE=`cat SUITE`

ret=`pwd`
rm -rf dist
mkdir -p dist/uck-$VERSION
cp -ar * dist/uck-$VERSION
cd dist/uck-$VERSION

# Caller and Key
if [ `id -nu` = wjg ]; then
	KEY=BA4B79B2
	CALLER="Wolf Geldmacher <wolf@womaro.ch>"
else
	KEY=063FFBAE
	CALLER="Fabrizio Balliano <fabrizio@fabrizioballiano.it>"
fi

# checking if version number has been updated everywhere
MAN_FILES=`ls docs/man/*.1 | wc -l`
MAN_FILES_WITH_VERSION=`grep "$VERSION" docs/man/*.1 | wc -l`
if [ $MAN_FILES -ne $MAN_FILES_WITH_VERSION ]; then
	echo "WARNING: you've to update version number in all man pages"
fi

if [ "`grep "$VERSION" debian/changelog | wc -l`" -eq "0" ]; then
	echo "WARNING: you've to update version number in debian/changelog"
	echo "WARNING: Creating temporary packages for testing purposes"

	# Add appropriate temporary header to debian/changelog
	( LANG=C
	  cat <<EOF
uck ($VERSION-0) $SUITE; urgency=low
  * New temporary test release
    - This is a build not meant for release. It is for testing only!
      For the real changes see the file /usr/share/doc/uck/changelog.gz

 -- $CALLER  `date -R`

EOF
	cat debian/changelog ) >debian/changelog.$$ &&
	mv debian/changelog.$$ debian/changelog
fi

# cleaning
tar zcf ../uck_$VERSION.orig.tar.gz .
rm -rf `find -name .svn`
rm -rf logo dist
rm -rf build.sh localbuild.sh Makefile SUITE

# generating deb package
case $1 in
-U)	# Upload
	dpkg-buildpackage -S -k$KEY
	( cd ..; dput ppa:uck-team/uck-unstable *.changes )
	;;
-S)	# Source release
	dpkg-buildpackage -S -k$KEY
	;;
*)	# Binary release
	dpkg-buildpackage -k$KEY
	;;
esac

# generating source package
rm -rf debian
cd ..
tar cfp uck_$VERSION.tar uck-$VERSION
gzip -9 uck_$VERSION.tar

cd "$ret"
