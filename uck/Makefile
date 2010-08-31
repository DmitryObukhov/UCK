#
# $Id$
#
all:

sdist: all
	rm -rf dist
	./localbuild.sh -S

upload: all
	rm -rf dist
	./localbuild.sh -U

dist: all
	./localbuild.sh

clean:
	rm -rf dist
