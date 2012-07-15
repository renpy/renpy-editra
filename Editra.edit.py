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
            s.close()
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

        env = dict(os.environ)

        def reset_env(name):
            original_name = "RENPY_ORIGINAL_" + name
            original_value = env.get(original_name, '')
            
            if original_value:
                env[name] = original_value
            else:
                env.pop(name, None)

        reset_env("LD_LIBRARY_PATH")
        reset_env("DYLIB_LIBRARY_PATH")
        reset_env("DYLD_FRAMEWORK_PATH")

        config_dir = os.path.join(DIR, ".Editra")

        if not os.path.exists(config_dir):
            os.mkdir(config_dir)

        plugin_cfg = os.path.join(config_dir, "plugin.cfg")
        if not os.path.exists(plugin_cfg):
            with open(plugin_cfg, "w") as f:
                f.write("renpy_editra=True")

        if renpy.windows:
            # No idea why startfile is required. I'm guessing it has something
            # to do with one py2exe process inside another's directory. 
            os.startfile(os.path.join(DIR, "Editra-win32/Editra.exe"))
        elif renpy.macintosh:
            subprocess.Popen([ "open", "-a", os.path.join(DIR, "Editra-mac.app") ], env=env)
        else:
            subprocess.Popen([ os.path.join(DIR, "Editra/editra") ], env=env)

    def end(self, **kwargs):
        if self.send_command():
            return
        
        self.launch_editra()
        
        deadline = time.time() + 10.0
        
        while time.time() < deadline:
            if self.send_command():
                return
        
            time.sleep(.1)
            
        raise Exception("Launching Editra failed.")
        
    
def main():
    e = Editor()
    e.begin()

    for i in sys.argv[1:]:
        e.open(i)

    e.end()
    
if __name__ == "__main__":
    main()
        
