import plugin

import profile
import editor
import daemon

class RenpyPlugin(plugin.Plugin):
    """
    We need this class so we load this module, but we don't actually use it
    for anything.
    """
    
    def __init__(self, *args, **kwargs):
        super(RenpyPlugin, self).__init__(*args, **kwargs)
        
        editor.init()
        profile.init()
        daemon.init()
    
    def GetName(self):
        return "Ren'Py Plugin"

