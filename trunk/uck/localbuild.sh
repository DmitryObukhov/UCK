#!/bin/bash
#
# Script to build a local version of the package
#
VERSION=`cat VERSION`
ret=`pwd`
rm -rf /tmp/uck-$VERSION
mkdir -p /tmp/uckbuild/uck-$VERSION
cp -ar . /tmp/uckbuild/uck-$VERSION
cd /tmp/uckbuild/uck-$VERSION

# checking if version number has been updated everywhere
MAN_FILES=`ls docs/man/*.1 | wc -l`
MAN_FILES_WITH_VERSION=`grep "$VERSION" docs/man/*.1 | wc -l`
if [ $MAN_FILES -ne $MAN_FILES_WITH_VERSION ]; then
	echo "WARNING: you've to update version number in all man pages"
fi

if [ "`grep "$VERSION" debian/changelog | wc -l`" -eq "0" ]; then
	echo "WARNING: you've to update version number in debian/changelog"
fi

# cleaning
rm -rf `find -name .svn`
rm -rf logo
rm -rf build.sh

# Add appropriate header to debian/changelog
(
  LANG=C
  cat <<EOF
uck ($VERSION-0test1) maverick; urgency=low
  * New test release

 -- Wolf Geldmacher <wolf@womaro.ch>  `date -R`

EOF
  cat debian/changelog ) >debian/changelog.$$ &&
mv debian/changelog.$$ debian/changelog

# generating deb package
dpkg-buildpackage -us -uc

# generating source package
rm -rf debian
cd ..
tar cfp uck_$VERSION.tar uck-$VERSION
gzip -9 uck_$VERSION.tar

cd "$ret"
cp /tmp/uckbuild/*.deb /tmp/uckbuild/*.gz .
rm -rf /tmp/uckbuild
