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

# cleaning
tar zcf ../uck_$VERSION.orig.tar.gz .
rm -rf `find -name .svn`
rm -rf logo dist
rm -rf build.sh localbuild.sh Makefile SUITE

# generating deb package
case $1 in
-U)	# Upload
	dpkg-buildpackage -S
	( cd ..; dput ppa:uck-team/uck-stable *.changes )
	echo "https://edge.launchpad.net/~uck-team/+archive/uck-stable/+copy-packages"
	;;
-S)	# Source release
	dpkg-buildpackage -S
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
