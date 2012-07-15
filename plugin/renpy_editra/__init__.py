import traceback
import plugin

try:
    import profile
    import editor
    import daemon
except:
    traceback.print_exc()
    raise

class RenpyPlugin(plugin.Plugin):
    """
    We need this class so we load this module, but we don't actually use it
    for anything.
    """
    
    def __init__(self, *args, **kwargs):
        super(RenpyPlugin, self).__init__()

        try:
            editor.init()
            profile.init()
            daemon.init()
        except:
            traceback.print_exc()
            raise
    
    def GetName(self):
        return "Ren'Py Plugin"

