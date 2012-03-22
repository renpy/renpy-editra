import socket
import threading
import json
import wx
import traceback

import ebmlib

PORT = 35033

def send_json(f, **kwargs):
    json.dump(kwargs, f)
    f.flush()

def process_file(window, d):
    filename = d["name"]
    
    # If the file is open in this window, reuse it. Otherwise, open it.
    for i in range(window.nb.GetPageCount()):
        page = window.nb.GetPage(i)
        if page.GetFileName() == filename:
            window.nb.ChangePage(i)
            break
    else:
        window.nb.OpenPage(ebmlib.GetPathName(filename), ebmlib.GetFileName(filename), quiet=True)

    window.nb.GoCurrentPage()
    buff = window.nb.GetCurrentCtrl()

    if d.get("revert", False):
        buff.RevertToSaved()

    # Go to the line.
    if "line" in d:
        buff.GotoLine(d["line"] - 1)


def process_core(d):
    app = wx.GetApp() #@UndefinedVariable
    
    new_window = d.get("new_window", False)
    files = d.get("files", [ ])
    
    if not files:
        raise Exception("Can't operate on empty file list.")


    # Find a window to show to the user.
    window = None

    if not new_window:
        main_windows = app.GetMainWindows()
        if main_windows:
            window = main_windows[0]
    
    if window is None:
        window = app.OpenNewWindow()

    # Present that window to the user.
    if window.IsIconized():
        window.Iconize(False)

    window.Raise()

    # Show the various files.
    for i in files:
        process_file(window, i)

    # Show the first file again, to be sure it has focus.
    process_file(window, files[0])
        

def process(s, f, d):
    try:
        try:    
            process_core(d)
            send_json(f)
        except Exception, e:
            traceback.print_exc()
            send_json(f, error=unicode(e))

    finally:
        f.close()
        s.close()
    

def server(s):
    f = s.makefile("r+")
    line = f.readline()
    
    try:
        d = json.loads(line)
        wx.CallAfter(process, s, f, d) #@UndefinedVariable
    
    except Exception, e:
        traceback.print_exc()
        send_json(f, error=unicode(e))

        f.close()
        s.close()


def listener():
    """
    A thread that listens for socket connections.
    """
    
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    s.bind(("127.0.0.1", PORT))
    s.listen(5)
    
    while True:
        ss, _addr = s.accept()
        
        t = threading.Thread(target=server, args=(ss,))
        t.daemon = True
        t.start()
    
    
t = threading.Thread(target=listener)
t.daemon = True
t.start()
