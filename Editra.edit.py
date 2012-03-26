#!/usr/bin/env python

import socket
import sys
import os
import subprocess
import threading
import time
import json

PORT = 35033

if "RENPY_BASE" in os.environ:
    sys.path.insert(0, os.environ["RENPY_BASE"])

import renpy.editor

class Editor(renpy.editor.Editor):

    def begin(self, new_window=False, **kwargs):
        self.command = { "new_window" : new_window, "files" : [ ] }
    
    def open(self, filename, line=None, **kwargs):

        d = { "name" : os.path.abspath(filename) }
        
        if line is not None:
            d["line"] = line
        
        self.command["files"].append(d)

    def send_command(self):
        """
        Tries connecting to editra and sending the command.
        
        Returns true if the command has been sent, and false if the command
        was not sent.
        """

        try:
            s = socket.socket()
            s.connect(("127.0.0.1", PORT))
        except socket.error:
            return False
        
        f = s.makefile("w+")
        json.dump(self.command, f)
        f.write("\n")
        f.flush()
        
        result = f.readline()
        
        if not result:
            raise Exception("Editra closed control channel.")
        
        result = json.loads(result)
        
        if "error" in result:
            raise Exception("Editra error: {0}".format(result["error"]))
        
        return True

    def launch_editra(self):
        """
        Tries to launch Editra.
        """

        DIR = os.path.abspath(os.path.dirname(__file__))

        if renpy.linux:
            subprocess.Popen([ os.path.join(DIR, "Editra/editra") ])
        elif renpy.linux:
            subprocess.Popen([ os.path.join(DIR, "Editra-win32/Editra.exe") ])
        elif renpy.macintosh:
            subprocess.Popen([ "open", "-a", os.path.join(DIR, "Editra-mac.app") ])

    def end(self, **kwargs):
        if self.send_command():
            return
        
        self.launch_editra()
        
        deadline = time.time() + 10.0
        
        while time.time() < deadline:
            if self.send_command():
                return
            
        raise Exception("Launching Editra failed.")
        
    
def main():
    e = Editor()
    e.begin()

    for i in sys.argv[1:]:
        e.open(i)

    e.end()
    
if __name__ == "__main__":
    main()
        
