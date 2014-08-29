#!/bin/bash

try () { "$@" || exit 1; }

VERSION="0.6.99"

setup () {
    try cd plugin
    export PYTHONPATH="../$1/plugins"
    # try python2.7 setup.py install --install-lib "../$1/plugins"
    rm -Rf dist
    try python2.7 setup.py bdist_egg
    try python2.6 setup.py bdist_egg
    try cd ..
    try cp plugin/dist/* "$1/plugins"
    try cp RenPy.ess "$1/styles/RenPy.ess"
    try cp "ren'py.rpy" "$1/tests/syntax"
    try rm "$1/plugins/"*py2.6*
}

D="dist/editra"

rm -Rf "$D/Editra"
rm -Rf "$D/Editra-mac.app"
try mkdir -p $D

# Windows
# try unzip -d "$D" "raw/Editra-win32.zip"
# try mv "$D/Editra" "$D/Editra-win32"
# setup "$D/Editra-win32"

# Linux
try tar xzf "raw/Editra-$VERSION.tar.gz" -C "$D"
try mv "$D/Editra-$VERSION" "$D/Editra"
try ./edit_shebang.py "$D/Editra/editra" "$D/Editra/Editra.pyw"
setup "$D/Editra"

# Mac OS X
# try unzip -d "$D" "raw/Editra.app.zip"
# try mv "$D/Editra.app" "$D/Editra-mac.app"
# setup "$D/Editra-mac.app/Contents/Resources"
try unzip -d "$D" "raw/Editra.app.zip"
try mv "$D/Editra.app" "$D/Editra-mac.app"
setup "$D/Editra-mac.app/Contents/Resources"

try cp "Editra.edit.py" "$D"

# Windows.
echo "Remember to build the windows version if it changed."
