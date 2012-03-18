import plugin
import profiler

import wx.stc #@UnresolvedImport
import time
import re

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

LANG_RENPY = u"Ren'Py"
EXTENSIONS = "rpy rpym"

# Styles.
(STC_RENPY_DEFAULT,
 STC_RENPY_COMMENT,
 STC_RENPY_STRING,
 STC_RENPY_KEYWORD,
 STC_RENPY_KEYWORD2) = range(5)

SYNTAX_ITEMS = [
    (STC_RENPY_DEFAULT, 'default_style'),
    (STC_RENPY_COMMENT, 'comment_style'),
    (STC_RENPY_STRING, 'string_style'),
    (STC_RENPY_KEYWORD, 'keyword_style'),
    (STC_RENPY_KEYWORD, 'keyword2_style'),
    ]

# What is the computed indentation of this line?
INDENT_MASK = 0xff

# What format is this line in?
LINE_MASK = 0xf00
LINE_RPY = 0x100
LINE_PY = 0x200

# What format should sub-blocks of this line be in?
BLOCK_MASK = 0x3000
BLOCK_RPY = 0x1000
BLOCK_PY = 0x2000

# Does this line cause an indent?
INDENTS = 0x4000
MAYBE_INDENTS = 0x8000

# Line start re. This is used to weed out comment lines and the like.
line_start_re = re.compile(r'(?P<indent> *)(?P<comment>\#.*)?(?P<eol>\r?\n)?')

# A regex that matches lines of Ren'Py code.
regex = re.compile(r'''
(?P<string>
  [ur]*\"(\\.|[^"\\])*\"
| [ur]*\'(\\.|[^'\\])*\'
| [ur]*\`(\\.|[^`\\])*\`
| [ur]*\"\"\"(\\.|[^"\\])*\"\"\"
| [ur]*\'\'\'(\\.|[^'\\])*\'\'\'
)
|(?P<word>
  \b(\w+)\b
| \$
)
|(?P<eol>
  \r?\n
)
|(?P<open_paren>
  \(
| \[
| \{
)
|(?P<close_paren>
  \)
| \]
| \}
)
|(?P<comment>
  \#.*
)
|(?P<default>
  \ +
| .
)
''', re.X)


renpy_python = re.compile(r'''
  init\s+(-?\d+\s+)?python
| python
''', re.X)

# A map from id(stc) to the line with the most valid line state in that STC.
# (GetMaxLineState can overreturn).
max_line_cache = { }

def StyleText(stc, start, end):
    """Style the text
    @param stc: Styled text control instance
    @param start: Start position
    @param end: end position

    """

    print
    print "Styling text", start, end
    start_time = time.time()

    # First, figure out the line based on the position.
    line = stc.LineFromPosition(start)

    # Find the start of the line that's been styled before this one.
    while line and stc.GetLineState(line) == 0:
        line -= 1

    # The indentation starting the current block. (None to indicate
    # it hasn't been set yet.)
    block_indent = 0

    # The type of block we're dealing with.
    block_type = BLOCK_RPY

    # Is this block's indentation optional?
    block_maybe_indents = False
    
    # A stack of outer blocks, giving the indent and type of those
    # blocks.
    block_stack = [ ]
    
    # Find the last line before line with a 0 indent. (Or the first 
    # line if we don't have one line that.)
    base_line = line
    while base_line > 0:
        base_line -= 1
        
        state = stc.GetLineState(base_line)
        
        if not state:
            continue
            
        indent = state & INDENT_MASK
        if indent == 0:
            break
    
    # Figure out what sort of block we're in, and build up the stack
    # of non-closed blocks.
    for i in range(base_line, line):
        state = stc.GetLineState(i)

        if not state:
            continue
    
        indent = state & INDENT_MASK

        if block_indent is None:
            block_indent = indent
            
        if state & INDENTS:
            block_stack.append((block_indent, block_type))
            block_indent = None
            block_type = state & BLOCK_MASK

        if state & MAYBE_INDENTS:
            block_maybe_indents = True
        else:
            block_maybe_indents = False
            
        while indent < block_indent:
            block_indent, block_type = block_stack.pop()

    # Clean out the old (no longer relevant) line states.
    for i in range(line, max_line_cache.get(id(stc), 0) + 1):
        stc.SetLineState(i, 0)

    new_start = stc.PositionFromLine(line)
    stc.StartStyling(new_start, 0xff)

    text = stc.GetTextRangeUTF8(new_start, end)
    len_text = len(text)
    pos = 0

    while pos < len_text:

        # The line and pos this statement begins on.
        statement_line = line

        m = line_start_re.match(text, pos)
        pos = m.end()
        
        indent = len(m.group('indent'))
        comment = m.group('comment')
        eol = m.group('eol')

        if eol:
            stc.SetStyling(indent, STC_RENPY_DEFAULT)

        # Style a line-long comment.
        if comment:
            stc.SetStyling(len(comment), STC_RENPY_COMMENT)
                    
        # If the line is empty, continue.
        if eol:
            stc.SetStyling(len(eol), STC_RENPY_DEFAULT)
            line += 1
            continue

        # Otherwise, we have a real line. Figure out the indentation of it.
        
        indent_indicator = 0

        # If we're indented from the previous line and starting a new block,
        # deal with that.
        if block_indent is None and indent > block_stack[-1][0]:
            block_indent = indent

        # Deal with empty blocks. Not an error, because of label.
        if block_indent is None:
            if not block_maybe_indents:
                indent_indicator = wx.stc.STC_INDIC2_MASK                
            block_indent, block_type = block_stack.pop()
            
        # We outdented, go out a block or more.
        while block_indent > indent:
            block_indent, block_type = block_stack.pop() 

        # Now check that we match the current block.
        if indent != block_indent:
            # Indentation error.
            indent_indicator = wx.stc.STC_INDIC2_MASK

        # Style the indentation.
        stc.SetStyling(indent, STC_RENPY_DEFAULT | indent_indicator)

        # Store the line type.
        line_type = block_type >> 4

        line_text = ""
        paren_depth = 0

        while True:
            m = regex.match(text, pos)
            if not m:
                break

            pos = m.end()

            # Rules for applying styling.
            string = m.group("string")
            if string:

                line_text += string
                line += string.count("\n")

                i = 0
                while string[i] in 'ur':
                    i += 1

                stc.SetStyling(i + 1, STC_RENPY_DEFAULT)
                stc.SetStyling(len(string) - 2 - i, STC_RENPY_STRING)
                stc.SetStyling(1, STC_RENPY_DEFAULT)

                continue

            word = m.group("word")                  
            if word:
                line_text += word

                # TODO: Decide keyword vs word.
                
                stc.SetStyling(len(word), STC_RENPY_DEFAULT)
                continue

            comment = m.group("comment")
            if comment:
                # Don't include comment text in line_text.                    
                stc.SetStyling(len(comment), STC_RENPY_COMMENT)
                continue

            # Style everything else.
            line_text += m.group(0)
            stc.SetStyling(len(m.group(0)), STC_RENPY_DEFAULT)

            # Rules for everything else.
            if m.group("open_paren"):
                paren_depth += 1
            elif m.group("close_paren"):
                paren_depth -= 1                    
            elif m.group("eol"):
                line += 1
                
                if not paren_depth:
                    break
                
                # End a runaway line, eventually.
                if len(line_text) > 8000:
                    break

        line_text = line_text.strip()

        block_maybe_indents = False

        if line_text and line_text[-1] == ':':
            block_stack.append((block_indent, block_type))
            block_indent = None
            
            indents = INDENTS

            if line_text.startswith("label"):
                indents |= MAYBE_INDENTS
                block_maybe_indents = True
                
            if line_type == LINE_RPY:
                block_type = BLOCK_RPY
                if renpy_python.match(line_text):
                    block_type = BLOCK_PY
            else:
                block_type = BLOCK_PY

        else:
            indents = 0
                    
        new_state = indent | line_type | block_type | indents
        stc.SetLineState(statement_line, new_state)

    max_line_cache[id(stc)] = line

    print "E", time.time() - start_time
    print "Style time:", time.time() - start_time, end
            

def AutoIndenter(stc, current_pos, indent_char):
    line = stc.LineFromPosition(current_pos)
    
    while line >= 0:
        state = stc.GetLineState(line)
    
        if state:
            break
        
        line -= 1
        
    # Ren'Py will only accept space for indentation, so always indent with
    # spaces.
    
    if state & INDENTS:
        indent = "\n" + " " * ((state & INDENT_MASK) + 4)
    else:
        indent = "\n" + " " * ((state & INDENT_MASK) + 0)
         
    return indent
    

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

        self.SetLexer(wx.stc.STC_LEX_CONTAINER)
        self.RegisterFeature(syntax.synglob.FEATURE_STYLETEXT, StyleText)
        # self.RegisterFeature(synglob.FEATURE_AUTOINDENT, AutoIndenter)

    def GetKeywords(self):
        return[ ]

    def GetSyntaxSpec(self):
        return SYNTAX_ITEMS

    def GetProperties(self):
        return [ ]

    def GetCommentPattern(self):
        return [u'#']

try:
    setup_profile()
    register_syntax()
except:
    import traceback
    traceback.print_exc()

