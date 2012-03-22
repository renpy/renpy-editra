#!/bin/bash

try () { "$@" || exit 1; }

VERSION="0.6.99"
REV="1"

setup () {
    try cd plugin
    export PYTHONPATH="../$1/plugins"    
    try python2.7 setup.py install --install-lib "../$1/plugins"
    try python2.6 setup.py install --install-lib "../$1/plugins"
    try cd ..
    try cp RenPy.ess "$1/styles/RenPy.ess"
    try cp "ren'py.rpy" "$1/tests/syntax"
}


# Linux
rm -Rf "dist/editra-linux-$VERSION-$REV"
try tar xzf "raw/Editra-$VERSION.tar.gz" -C dist
try mv "dist/Editra-$VERSION" "dist/editra-linux-$VERSION-$REV"
setup "dist/editra-linux-$VERSION-$REV"

# Windows
rm -Rf "dist/editra-win32-$VERSION-$REV"
try unzip -d "dist" "raw/Editra-win32.zip"
try mv "dist/Editra" "dist/editra-win32-$VERSION-$REV"
setup "dist/editra-win32-$VERSION-$REV"

# Mac OS X
rm -Rf "dist/Editra.app"
try unzip -d "dist" "raw/Editra.app.zip"
setup "dist/Editra.app/Contents/Resources"

# Pack up.
try cd dist
rm -f "editra-win32-$VERSION-$REV.zip"
zip -9r "editra-win32-$VERSION-$REV.zip" "editra-win32-$VERSION-$REV"

rm -f "editra-mac-$VERSION-$REV.zip"
zip -9r "editra-mac-$VERSION-$REV.zip" "Editra.app"

tar cvjf "editra-linux-$VERSION-$REV.tar.bz2" "editra-linux-$VERSION-$REV"
