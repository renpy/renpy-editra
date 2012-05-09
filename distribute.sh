#!/bin/bash

cd dist

D="/home/tom/ab/website/renpy/dl/editra"

rm "$D/editra-$1-win32.zip"
zip -9r  "$D/editra-$1-win32.zip" editra/Editra-win32 editra/Editra.edit.py

rm "$D/editra-$1-mac.zip"
zip -9r  "$D/editra-$1-mac.zip" editra/Editra-mac.app editra/Editra.edit.py

rm "$D/editra-$1-linux.zip"
zip -9r  "$D/editra-$1-linux.zip" editra/Editra editra/Editra.edit.py
