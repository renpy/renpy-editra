import profiler
import wx.stc #@UnresolvedImport
import re

import keywords
import keyword

RENPY_KEYWORDS = set(keywords.keywords)
RENPY_PROPERTIES = set(keywords.properties)
PYTHON_KEYWORDS = set(keyword.kwlist)

# Do we style indentation errors?
INDENT_ERRORS = False

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
    (STC_RENPY_KEYWORD2, 'keyword2_style'),
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

class StyleBuffer(object):
    """
    Buffers runs of styling to be applied all at once.
    """
    
    def __init__(self, stc, start, bits):
        self.stc = stc
        self.start = start
        self.bits = bits

        self.started = False
        self.buffer = [ ]

    def style(self, length, style):
        self.buffer.append((length, style))
        
    def apply(self, ):
        
        stc = self.stc
        start = self.start
        
        if not self.started:
            stc.StartStyling(self.start, self.bits)
            
        for length, style in self.buffer:
            stc.SetStyling(length, style)
            start += length

        self.buffer = [ ]
        self.start = start


def StyleText(stc, start, end):
    """Style the text
    @param stc: Styled text control instance
    @param start: Start position
    @param end: end position
    """

    max_styled_line = max_line_cache.get(id(stc), 0)

    # Set up the bad indentation indicator style.
    if stc.IndicatorGetStyle(1) != wx.stc.STC_INDIC_SQUIGGLE:
        stc.IndicatorSetStyle(1, wx.stc.STC_INDIC_SQUIGGLE)
        stc.IndicatorSetForeground(1, "#FF0000")

    # A change to one line can change others below it. So we restyle all 
    # visible text with any change. (We restyle a bit more so we don't get
    # caught in things like triple-quoted strings.)
    try:        
        vis_end_line = stc.GetLastVisibleLine() + 20
    except:
        # Fails if we're in the preview.
        vis_end_line = stc.GetLineCount()
        
    vis_end_pos = stc.GetLineEndPosition(vis_end_line)
    end = max(end, vis_end_pos)

    # First, figure out the line based on the position.
    line = stc.LineFromPosition(start)

    # Jump back a bunch of lines, so that we always restyle the entire
    # screen.
    line = min(line - 60, max_styled_line)
    if line < 0:
        line = 0

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

    if base_line < 0:
        base_line = 0
    
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
    for i in range(line, max_styled_line + 1):
        stc.SetLineState(i, 0)

    new_start = stc.PositionFromLine(line)
    text = stc.GetTextRangeUTF8(new_start, end)

    # End open strings.
    text += "\n\"\"\"'''"
    
    len_text = len(text)
    pos = 0

    # stc.StartStyling(new_start, 0xff & (~wx.stc.STC_INDIC2_MASK))
    sb = StyleBuffer(stc, new_start, 0xff & (~wx.stc.STC_INDIC2_MASK))


    while pos < len_text:

        # The line and pos this statement begins on.
        statement_line = line

        m = line_start_re.match(text, pos)
        pos = m.end()
        
        indent = len(m.group('indent'))
        comment = m.group('comment')
        eol = m.group('eol')

        if eol:
            sb.style(indent, STC_RENPY_DEFAULT)

        # Style a line-long comment.
        if comment:
            sb.style(len(comment), STC_RENPY_COMMENT)
                    
        # If the line is empty, continue.
        if eol:
            sb.style(len(eol), STC_RENPY_DEFAULT)
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
            if INDENT_ERRORS and not block_maybe_indents:
                indent_indicator = wx.stc.STC_INDIC1_MASK                
            block_indent, block_type = block_stack.pop()
            
        # We outdented, go out a block or more.
        while block_indent > indent:
            block_indent, block_type = block_stack.pop() 

        # Now check that we match the current block.
        if INDENT_ERRORS and indent != block_indent:
            # Indentation error.
            indent_indicator = wx.stc.STC_INDIC1_MASK

        # Style the indentation.
        sb.style(indent, STC_RENPY_DEFAULT | indent_indicator)

        # Store the line type.
        line_type = block_type >> 4

        line_text = ""
        paren_depth = 0

        while True:
            m = regex.match(text, pos)
            if not m:
                break

            pos = m.end()

            if pos > len_text:
                pos = len_text

            # Rules for applying styling.
            string = m.group("string")
            if string:

                line_text += string
                line += string.count("\n")

                i = 0
                while string[i] in 'ur':
                    i += 1

                sb.style(i + 1, STC_RENPY_DEFAULT)
                sb.style(len(string) - 2 - i, STC_RENPY_STRING)
                sb.style(1, STC_RENPY_DEFAULT)

                continue

            word = m.group("word")                  
            if word:
                line_text += word

                style = STC_RENPY_DEFAULT
                
                if line_type == LINE_RPY:
                    if word in RENPY_KEYWORDS:
                        style = STC_RENPY_KEYWORD
                    elif word in RENPY_PROPERTIES:
                        style = STC_RENPY_KEYWORD2

                elif line_type == LINE_PY:
                    if word in PYTHON_KEYWORDS:
                        style = STC_RENPY_KEYWORD

                sb.style(len(word), style)
                continue

            comment = m.group("comment")
            if comment:
                # Don't include comment text in line_text.                    
                sb.style(len(comment), STC_RENPY_COMMENT)
                continue

            # Style everything else.
            line_text += m.group(0)
            sb.style(len(m.group(0)), STC_RENPY_DEFAULT)

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

    sb.apply()
    max_line_cache[id(stc)] = line


def AutoIndenter(stc, current_pos, indent_char):
    """
    Determines the indentation rule.
    
    0) If the line is empty except for whitespace, indent to the current
       column.
    
    1) If all strings and parenthesis are closed, then indent based on how 
       this line has been styled.
       
    2) If we're in a string, indent to one more than the position at 
       which the string started. 
       
    3) If we've opened more parenthesis then we closed on the current
       line, indent by 1.
       
    4) If we've closed more parenthesis than we opened on the current
       line, dedent by 1.
       
    5) Otherwise, keep the current indentation.
    """
    
    line = stc.LineFromPosition(current_pos)

    while line >= 0:
        line_state = stc.GetLineState(line)
    
        if line_state:
            break
        
        line -= 1

    start = stc.PositionFromLine(line)
    text = stc.GetTextRangeUTF8(start, current_pos)

    pos = -1
    len_text = len(text)
    
    # States for the indenting state machine.    
    ISTATE_INDENT = 0 # Line indentation.
    ISTATE_CODE = 1 # Normal code.
    ISTATE_COMMENT = 2 # Comment. 
    ISTATE_COMMENT_LINE = 3 # Full-line comment.
    ISTATE_STRING = 4 # In a string.
    ISTATE_EOL = 5 # At the end of the line.
        
    state = ISTATE_EOL
    
    # The indentation of the last non-blank, non-comment line.
    prior_indent = 0

    # The number of parens that are open in the statement.
    open_parens = 0
    
    # The net change in parens on the current line.
    net_parens = 0

    # Where the current line started.
    line_start = 0

    # The quote characters used to close the current string.
    quote_chars = None
        
    # The indentation to use if we're in a quote.
    quote_indent = 0

    while pos + 1 < len_text:
        
        pos += 1        
        c = text[pos]
        
        if state == ISTATE_EOL:
            line_start = pos
            net_parens = 0
            state = ISTATE_INDENT
            
        if state == ISTATE_INDENT:
            
            if c == " ":
                continue
            
            elif c == "\n":
                state = ISTATE_EOL
                continue
            
            elif c == "#":
                state = ISTATE_COMMENT_LINE
                continue
            
            state = ISTATE_CODE
            prior_indent = pos - line_start
            
            # Intentionally fall through.
            
        if state == ISTATE_COMMENT or state == ISTATE_COMMENT_LINE:
            
            if c == "\n":
                state = ISTATE_EOL
                continue
            
            continue

        elif state == ISTATE_CODE:
            
            if c == "\n":
                state = ISTATE_EOL
                continue
            
            if c in "\"'`":

                start = text[pos:pos + 3]
                
                if start == "'''" or start == '"""':
                    quote_chars = start
                    quote_indent = pos - line_start
                    pos += 2
                    state = ISTATE_STRING
                    continue
                
                quote_chars = c
                quote_indent = 1 + pos - line_start
                state = ISTATE_STRING
                continue
                
            if c in "([{":
                net_parens += 1
                open_parens += 1
                continue
                
            if c in ")]}":
                net_parens -= 1
                open_parens -= 1
                continue
          
            if c == "#":
                state = ISTATE_COMMENT
                continue
            
            continue
        
        elif state == ISTATE_STRING:
        
            if c == "\n":
                line_start = pos + 1
                continue
            
            if c == "\\":
                pos += 1
                continue

            if c == quote_chars:
                state = ISTATE_CODE
                continue

            if text[pos:pos + 3] == quote_chars:
                pos += 2
                state = ISTATE_CODE
                continue
            
            continue

    # Compute the indent of the line itself.
    INDENTWIDTH = profiler.Profile_Get("INDENTWIDTH")
    line_indent = line_state & INDENT_MASK
  
    if state == ISTATE_STRING:
        indent = quote_indent

    elif state == ISTATE_COMMENT_LINE:
        l = stc.GetCurrentLine()
        indent = stc.GetLineIndentation(l)

    elif open_parens <= 0:
        if state == ISTATE_INDENT or state == ISTATE_EOL:
            l = stc.GetCurrentLine()
                        
            if stc.GetLineIndentPosition(l) == stc.GetLineEndPosition(l):
                indent = stc.GetColumn(current_pos)
            else:
                indent = line_indent
                
        elif line_state & INDENTS:
            indent = line_indent + INDENTWIDTH
        else:
            indent = line_indent
 
    elif net_parens > 0:
        indent = prior_indent + INDENTWIDTH
    elif net_parens < 0:
        indent = max(line_indent + INDENTWIDTH, prior_indent - INDENTWIDTH)
    else:
        indent = prior_indent
      
    # Implement the indent.
    eolch = stc.GetEOLChar()    
    stc.AddText(eolch)

    l = stc.GetCurrentLine()
    stc.SetLineIndentation(l, indent)
    stc.GotoPos(stc.GetLineIndentPosition(l))
    

def register_syntax():
    
    global ID_LANG_RENPY
    ID_LANG_RENPY = syntax.syntax.RegisterNewLangId("LANG_RENPY", LANG_RENPY)

    syntax.synglob.ID_LANG_RENPY = ID_LANG_RENPY
    syntax.synglob.LANG_RENPY = LANG_RENPY
    
    # Register file extensions with extension register
    syntax.synextreg.ExtensionRegister().Associate(LANG_RENPY, EXTENSIONS)

    syntax.synextreg.EXT_MAP['rpy rpym'] = LANG_RENPY

    # Update static syntax id list
    if ID_LANG_RENPY not in syntax.syntax.SYNTAX_IDS:
        syntax.syntax.SYNTAX_IDS.append(ID_LANG_RENPY)

    syntax.synglob.LANG_MAP[LANG_RENPY] = ( ID_LANG_RENPY, "renpy_editra.editor")


class SyntaxData(syntax.syndata.SyntaxDataBase):
    """SyntaxData object for Python""" 
    def __init__(self, langid):
        super(SyntaxData, self).__init__(langid)

        # Setup

        self.SetLexer(wx.stc.STC_LEX_CONTAINER)
        self.RegisterFeature(syntax.synglob.FEATURE_STYLETEXT, StyleText)
        self.RegisterFeature(syntax.synglob.FEATURE_AUTOINDENT, AutoIndenter)

    def GetKeywords(self):
        return [ ]

    def GetSyntaxSpec(self):
        return SYNTAX_ITEMS

    def GetProperties(self):
        return [ ]

    def GetCommentPattern(self):
        return [u'#']

def init():
    register_syntax()

