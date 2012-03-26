#!/bin/bash

try () { "$@" || exit 1; }

VERSION="0.6.99"
REV="2"

setup () {
    try cd plugin
    export PYTHONPATH="../$1/plugins"    
    try python2.7 setup.py install --install-lib "../$1/plugins"
    try python2.6 setup.py install --install-lib "../$1/plugins"
    try cd ..
    try cp RenPy.ess "$1/styles/RenPy.ess"
    try cp "ren'py.rpy" "$1/tests/syntax"
}

D="dist/editra"

rm -Rf "$D"

# Windows
try unzip -d "$D" "raw/Editra-win32.zip"
try mv "$D/Editra" "$D/Editra-win32"
setup "$D/Editra-win32"

# Linux
try tar xzf "raw/Editra-$VERSION.tar.gz" -C "$D"
try mv "$D/Editra-$VERSION" "$D/Editra"
setup "$D/Editra"

# Mac OS X
try unzip -d "$D" "raw/Editra.app.zip"
try mv "$D/Editra.app" "$D/Editra-mac.app"
setup "$D/Editra-mac.app/Contents/Resources"

try cp "Editra.edit.py" "$D"