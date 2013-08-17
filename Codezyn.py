from spark import GenericScanner, GenericASTBuilder, GenericASTTraversal
from ast import AST
#Scanner Class(es)

class Token():
    "Simple class to store tokens"
    def __init__(self, c = -1, t = "", m = ""):
        self.code = c
        self.type = t
        self.match = m
        self.string = ""
    
    def __cmp__(self, o):
        return cmp(self.type, o)
        
    def __str__(self):
        return self.match
        
class CodezynBaseScanner(GenericScanner):
    "Basic Lexer/Scanner class"
    
    def __init__(self):
        GenericScanner.__init__(self)
        
    def tokenize(self,input):
        self.tl = []
        GenericScanner.tokenize(self, input)
        return self.tl
    
    def t_whitespace(self, s):
        r" \s+ "
        pass

    def t_identifier(self, s):
        r" [_A-Za-z][\-_A-Za-z0-9]* "
        self.tl.append(Token(2,"Identifier",s))

    def t_eos(self, s):
        r" ; "
        self.tl.append(Token(3,"EndOfStatement",s)) 
        
    def t_number(self,s):
        r" [0-9]+ "
        self.tl.append(Token(18,"Number",s))
            
    def t_assignment(self, s):
        r" \= "
        self.tl.append(Token(8,"Assignment",s))
        
    def t_literal(self, s):
        r" \"([^\"\\\\]|\\\\.)*\" "
        self.tl.append(Token(9,"Literal",s))

    def t_paramseparator(self, s):
        r" , "
        self.tl.append(Token(10,"ParameterSeparator",s))
    
    def t_access(self, s):
        r" \. "
        self.tl.append(Token(16,"AccessOperator",s))
        
    def t_ropen(self, s):
        r" \( "
        self.tl.append(Token(11,"RoundOpen",s))

    def t_rclose(self, s):
        r" \) "
        self.tl.append(Token(12,"RoundClose",s))

    def t_copen(self, s):
        r" \{ "
        self.tl.append(Token(13,"CurlyOpen",s))

    def t_cclose(self, s):
        r" \} "
        self.tl.append(Token(14,"CurlyClose",s))        

    def t_sopen(self, s):
        r" \[ "
        self.tl.append(Token(19,"SquareOpen",s))

    def t_sclose(self, s):
        r" \] "
        self.tl.append(Token(20,"SquareClose",s))

class CodezynExtendedScanner(CodezynBaseScanner):
    "Extended Lexer/Scanner for reserved words and numbers (greater priority)"

    def __init__(self):
        CodezynBaseScanner.__init__(self)

    def t_tag(self, s):
        r" \<(a|abbr|acronym|address|applet|area|b|base|basefont|bdo|big|blockquote|body|br|button|caption|center|cite|code|col|colgroup|dd|del|dfn|dir|div|dl|dt|em|fieldset|font|form|frame|frameset|h1|h2|h3|h4|h5|h6|head|hr|html|i|iframe|img|input|ins|isindex|kbd|label|legend|li|link|map|menu|meta|noframes|noscript|object|ol|optgroup|option|p|param|pre|q|s|samp|script|select|small|span|strike|strong|style|sub|sup|table|tbody|td|textarea|tfoot|th|thead|title|tr|tt|u|ul|var)\> "
        self.tl.append(Token(5,"HTMLTag",s))
        
class CodezynScanner(CodezynExtendedScanner):
    "First priority Lexer/Scanner"

    def __init__(self):
        CodezynExtendedScanner.__init__(self)
    
    def t_filetype(self, s):
        r" (template|generator) "
        self.tl.append(Token(1,"FileType",s))
        
    def t_scope(self, s):
        r" (public|private) "
        self.tl.append(Token(4,"Scope",s))
    
    def t_accessible(self, s):
        r" (\.content) "
        self.tl.append(Token(17,"ClassAccessible",s))

    def t_begin(self, s):
        r" (\.begin) "
        self.tl.append(Token(21,"Begin",s))

    def t_end(self, s):
        r" (\.end) "
        self.tl.append(Token(22,"End",s))        

    def t_txt(self, s):
        r'( \[ ( . | \n )+? \] )'
        self.tl.append(Token(23,"Text",s))                
#Parser Class(es)

class CodezynTemplateBuilder(GenericASTBuilder):
    "Codezyn Context Free Grammar Rules."
    def p_PROGRAM(self, args):
        '''
        PROGRAM ::= DECLARATION STATEMENT
        DECLARATION ::= FileType Identifier EndOfStatement
        ARGUMENT ::= Identifier Assignment Literal
        ARGUMENT ::= ARGUMENT ParameterSeparator ARGUMENT
        PARAMETER ::= Literal
        PARAMETER ::= Number
        PARAMETER ::= PARAMETER ParameterSeparator PARAMETER
        FUNCTION ::= Scope HTMLTag Identifier RoundOpen RoundClose CurlyOpen CurlyClose
        FUNCTION ::= Scope HTMLTag Identifier RoundOpen RoundClose CurlyOpen STATEMENT CurlyClose
        FUNCTION ::= Scope HTMLTag Identifier RoundOpen ARGUMENT RoundClose CurlyOpen  CurlyClose
        FUNCTION ::= Scope HTMLTag Identifier RoundOpen ARGUMENT RoundClose CurlyOpen STATEMENT CurlyClose
        CALLFUNCTION ::= Identifier RoundOpen PARAMETER RoundClose
        STATEMENT ::= FUNCTION
        STATEMENT ::= CALLFUNCTION EndOfStatement
        STATEMENT ::= STATEMENT STATEMENT
        '''
class CodezynGeneratorBuilder(GenericASTBuilder):
    "Codezyn Context Free Grammar Rules."
    def p_PROGRAM(self, args):
        '''
        PROGRAM ::= DECLARATION STATEMENT
        DECLARATION ::= FileType Identifier EndOfStatement
        STATEMENT ::= Identifier Text
        STATEMENT ::= STATEMENT STATEMENT
        '''
class CodezynGeneratorTraverser(GenericASTTraversal):
    def n_STATEMENT(self,node):
        if node[0] == "Identifier":
            node.dict = { node[0].match : node[1].match[1:-1] }
        else: 
            node.dict = {}
            if hasattr(node[0],'dict'):
               for key in node[0].dict:
                    node.dict[key] = node[0].dict[key]      
            if hasattr(node[1],'dict'):
               for key in node[1].dict:
                    node.dict[key] = node[1].dict[key]

class CodezynTemplateTraverser(GenericASTTraversal):
    "Codezyn Traverser."
    def __init__(self,ast):
        GenericASTTraversal.__init__(self,ast)

    def n_FUNCTION(self,node):
        node.attributes = {}
        node.css = {}
        node.internal = []
        for n in node:
            if n == "ARGUMENT":
                node.attributes = n.attributes
            elif n == "STATEMENT":
                if hasattr(n,'css'):
                    node.css = n.css
                if hasattr(n,'internal'):
                    node.internal = n.internal
                
                
    def n_STATEMENT(self,node):
        if node[0] == "CALLFUNCTION":
            node.css = node[0].css
        elif node[0] == "FUNCTION":
            node.internal = [ node[0] ]
        elif node[0] == "STATEMENT":
            node.internal = []
            node.css = {}
            if hasattr(node[0],'internal'):
                node.internal += node[0].internal
            if hasattr(node[1],'internal'):
                node.internal += node[1].internal
            if hasattr(node[0],'css'):
               for key in node[0].css:
                    node.css[key] = node[0].css[key]      
            if hasattr(node[1],'css'):
               for key in node[1].css:
                    node.css[key] = node[1].css[key]      

    def n_CALLFUNCTION(self,node):
        node.css = { node[0].match : node[2].parameters }
        
    def n_PARAMETER(self, node):
        if node[0] == "PARAMETER":
            node.parameters = []
            node.paramaters = node[0].parameters + node[2].parameters
        else:
            node.parameters = [node[0].match]
        
    def n_ARGUMENT(self, node):
        if node[0] == "ARGUMENT":
            node.attributes = {}
            for key in node[0].attributes:
                node.attributes[key] = node[0].attributes[key]
            for key in node[2].attributes:
                node.attributes[key] = node[2].attributes[key]
        else:
            node.attributes = {node[0].match : node[2].match}
            
