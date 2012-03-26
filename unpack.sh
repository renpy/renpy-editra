#!/bin/bash
# Unpacks Editra, and then sets up the Ren'Py plugin in development mode.

VERSION="0.6.99"

try () { "$@" || exit 1; }

rm -Rf Editra

try tar xzf "raw/Editra-$VERSION.tar.gz"
try mv "Editra-$VERSION" "Editra"

try cd plugin
export PYTHONPATH=../Editra/plugins/
try python setup.py develop --install-dir=../Editra/plugins/
try cd ..

try ln -s ../../RenPy.ess Editra/styles/RenPy.ess
try ln -s "../../../ren'py.rpy" "Editra/tests/syntax/ren'py.rpy"
try ln -s ../Editra.edit.py Editra/Editra.edit.py
