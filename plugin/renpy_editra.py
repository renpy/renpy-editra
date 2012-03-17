import plugin
import profiler

import wx.stc as stc #@UnresolvedImport


############################################################################### 
# Dummy Plugin (So we load.)

class RenpyPlugin(plugin.Plugin):
    
    def GetName(self):
        return "Ren'Py Plugin (Dummy)"
    

############################################################################### 
# Change some of the default settings in the profile.

def setup_profile():

    version = profiler.Profile_Get("RENPY_VERSION", default=0)
    
    if version < 1:    
        profiler.Profile_Set("APPSPLASH", False)
    
    if version < 2:
        profiler.Profile_Set("CHECKUPDATE", False)
        profiler.Profile_Set("AALIASING", True)

        # Set the RENPY_VERSION setting to store the version of 
        # the Ren'Py profile in use.
    
        profiler.Profile_Set("RENPY_VERSION", 2)
    

############################################################################### 
# Create a Ren'Py Syntax.

import syntax

LANG_RENPY = "Ren'Py"
EXTENSIONS = "rpy rpym"

FOLD = ("fold", "1")
FOLD_QUOTES = ("fold.quotes.python", "1")
FOLD_COMMENTS = ("fold.comment.python", "1")
TIMMY = ("tab.timmy.whinge.level", "1")


def register_syntax():
    
    global ID_LANG_RENPY
    ID_LANG_RENPY = syntax.syntax.RegisterNewLangId("LANG_RENPY", LANG_RENPY)

    syntax.synglob.ID_LANG_RENPY = ID_LANG_RENPY
    syntax.synglob.LANG_RENPY = LANG_RENPY
    
    # Register file extensions with extension register
    syntax.synextreg.ExtensionRegister().Associate(LANG_RENPY, EXTENSIONS)

    # Update static syntax id list
    if ID_LANG_RENPY not in syntax.syntax.SYNTAX_IDS:
        syntax.syntax.SYNTAX_IDS.append(ID_LANG_RENPY)

    syntax.synglob.LANG_MAP[LANG_RENPY] = ( ID_LANG_RENPY, "renpy_editra")


class SyntaxData(syntax.syndata.SyntaxDataBase):
    """SyntaxData object for Python""" 
    def __init__(self, langid):
        super(SyntaxData, self).__init__(langid)

        # Setup

        self.SetLexer(stc.STC_LEX_CONTAINER)
        self.RegisterFeature(syntax.synglob.FEATURE_STYLETEXT, self.StyleText)
        # self.RegisterFeature(synglob.FEATURE_AUTOINDENT, AutoIndenter)


    def GetKeywords(self):
        """Returns Specified Keywords List """
        return ["foo bar" , "baz baka"]

    def GetSyntaxSpec(self):
        """Syntax Specifications """
        return [ (1, "foo_bar" ) ]

    def GetProperties(self):
        """Returns a list of Extra Properties to set """
        return [FOLD, TIMMY, FOLD_QUOTES, FOLD_COMMENTS]

    def GetCommentPattern(self):
        """Returns a list of characters used to comment a block of code """
        return [u'#']

    def StyleText(self, stc, start, end):
        print "Styling Text", start, "to", end
        
try:
    setup_profile()
    register_syntax()
except:
    import traceback
    traceback.print_exc()

