import plugin

class RenpyPlugin(plugin.Plugin):
    """
    We need this class so we load this module, but we don't actually use it
    for anything.
    """
    
    def GetName(self):
        return "Ren'Py Plugin (Dummy)"

# Import the rest of the plugin. This is what actually does something.

import profile
import editor
