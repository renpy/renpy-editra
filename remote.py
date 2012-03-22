import socket
import json
import sys

command = { 
    "new_window" : False,
    "files" : [ ]
    }


line = None

for i in sys.argv[1:]:
    
    try:
        line = int(i)
        continue
    except:
        pass
    
    filedict = { "name" : i }
    if line is not None:
        filedict["line"] = line
        line = None
    
    command["files"].append(filedict)
    

s = socket.socket()
s.connect(("127.0.0.1", 35033))
f = s.makefile("w+")

cmd = json.dumps(command)
print repr(cmd)
f.write(cmd + "\n")
f.flush()

d = json.load(f)
print d