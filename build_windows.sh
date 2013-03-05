#!/bin/bash
try () { "$@" || exit 1; }

try python -OO /t/ab/renpy-deps/renpython/build.py \
	windows-i686 \
	/t/ab/editra/dist/editra \
	Editra/src/Editra.py \
	--encodings --command editra

try python -OO /t/ab/renpy-deps/renpython/merge.py \
  /t/ab/editra/dist/editra \
  windows-i686
    
try rm -Rf /t/ab/editra/dist/editra/build

echo This needs to run inside the newbuild environment.