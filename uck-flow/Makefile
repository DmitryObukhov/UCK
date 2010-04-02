#
# $Id$
#
VERSION=0.3

all: translations

install: all
	$(MAKE) dist; \
	cd dist; \
	tar xvf UckFlow-$(VERSION).tar.gz; \
	cd UckFlow-$(VERSION); \
	sudo python ./setup.py install; \
	cd ..; \
	# sudo rm -rf UckFlow-$(VERSION)
	cd uck-patches; $(MAKE) $@

dist: FRC
	python setup.py sdist

clean:
	rm -f src/*.bak src/*.py[co] src/uckFlow.glade.h uckFlow.glade.h
	rm -f glademessage.pot
	sudo rm -rf dist
	rm -rf locale

messages.pot: src/uckFlow.glade uck-flow src/*.py
	xgettext -L python -k_ -kN_ -o messages.pot uck-flow src/*.py
	intltool-extract --type=gettext/glade src/uckFlow.glade
	mv src/uckFlow.glade.h .
	xgettext -k_ -kN_ -o glademessages.pot *.h
	echo "" >>messages.pot
	sed <glademessages.pot >>messages.pot '1,/^$$/d'
	rm -f uckFlow.glade.h glademessages.pot
	# Add new language: "LANG=xx_YY msginit"
	# Merge changes: "msgmerge -U xx.po messages.pot"

translations:
	for i in de; do \
		mkdir -p locale/$$i/LC_MESSAGES/; \
		msgfmt $$i.po -o locale/$$i/LC_MESSAGES/uckFlow.mo; \
	done

ci checkin: clean
	cvs ci -m"Intermediate" || true

FRC:
