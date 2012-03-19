#!/bin/bash
# Unpacks Editra, and then sets up the Ren'Py plugin in development mode.

VERSION="0.6.89"

try () { "$@" || exit 1; }

rm -Rf Editra

try tar xzf "Editra-$VERSION.tar.gz"
try mv "Editra-$VERSION" "Editra"

try cd plugin
export PYTHONPATH=../Editra/plugins/
try python setup.py develop --install-dir=../Editra/plugins/
try cd ..

try ln -s ../../RenPy.ess Editra/styles/RenPy.ess
