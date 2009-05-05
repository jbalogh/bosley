#!/bin/sh

# Pass any virtualenv args in with $*.

virtualenv --no-site-packages $* .
bin/easy_install pip
STATIC_DEPS=true bin/pip install -r reqs.txt
