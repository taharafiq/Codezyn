from Codezyn import CodezynScanner, Token, CodezynTemplateBuilder, CodezynTemplateTraverser, CodezynGeneratorBuilder, CodezynGeneratorTraverser
from csslist import cssList
import sys
from ast import AST

#Functions---------------------------------------------------------

def printTree(node, depth=0):
    file.write("%2d" %depth + "_"*depth + '<<'+node.type + '>>' + "\n")
    if hasattr(node,'_kids'):
        for n in node._kids:
            printTree(n, depth+1)

def checkRequiredTags(t,r):
    if t[1].match in r:
        r[t[1].match] = True
    for i in t.internal:
        checkRequiredTags(i,r)

def getValidTagIdentifiers(t):
    validIdentifiers.append(t[2].match)
    for i in t.internal:
        getValidTagIdentifiers(i)

def checkCSS(t):
    for c in t.css:
        if not c in cssList:
            print ("Codezyn Error: Invalid CSS property '" + c + "'.")
            exit()
    for i in t.internal:
        checkCSS(i)
        
def generateCode(node):
    cssString = ""
    htmlString = ""

    if "id" in node.attributes:
        cssString += "#" + node.attributes["id"][1:-1]
    elif "class" in node.attributes:
        cssString += "." + node.attributes["class"][1:-1]
    else:
        cssString += node[1].match[1:-1]
    
    cssString += " { \n"

    for key in node.css:
        cssString += "\t" + key + ": "
        cssString += node.css[key][0][1:-1] + "; \n"
    cssString += "} \n"
    
    fileCSS.write(cssString)
    if node[0].match == "public":
        htmlString+= "<" + node[1].match[1:-1]
        for key in node.attributes:
            htmlString+= " " + key + "=" + node.attributes[key]
       
        htmlString += "> \n"

        fileHTML.write(htmlString)

        if node[1].match == "<head>":
            fileHTML.write("<link rel=\"stylesheet\" type=\"text/css\" href=\"" + forCSS[-1] + ".css\" /> \n")

        if node[2].match in contentList:
            fileHTML.write(contentList[node[2].match])

        for i in node.internal:
            generateCode(i)
        
        fileHTML.write("</"  + node[1].match[1:-1] + "> \n")

#-----------------------------------------------------------------

argv = sys.argv
if len(argv) < 2:
    print "Codezyn Error: Required argument missing."
    exit()


#Tokenizing the input files
tokens_t = CodezynScanner().tokenize(open(argv[1] + ".czf").read())
tokens_g = CodezynScanner().tokenize(open(argv[1] + ".czg").read())

#Writing the token stream to file
# file = open(argv[1] + ".czt",'w')
# file.write("TEMPLATE TOKENS ---> \n\n")
# for token in tokens_t:
    # file.write(str(token.code) + ": " + token.type + " [" + token.match + "]\n")
# file.write("\nGENERATOR TOKENS ---> \n\n")
# for token in tokens_g:
    # file.write(str(token.code) + ": " + token.type + " [" + token.match + "]\n")    
# print "Codezyn Message: See " + argv[1] + ".czt for token stream."

#Creating the syntax tree                

tree = CodezynTemplateBuilder(AST,'PROGRAM').parse(tokens_t)
tree_g = CodezynGeneratorBuilder(AST,'PROGRAM').parse(tokens_g)

#Writing the syntax tree to file

# file = open(argv[1] + ".czp",'w')
# file.write("Template Tree ---> \n\n")
# printTree(tree)
# file.write("\n Generator Tree ---> \n\n")
# printTree(tree_g)
# file.close()
# print "Codezyn Message: See " + argv[1] + ".czp for syntax tree."

#Annotating the tree
CodezynTemplateTraverser(tree).postorder()
CodezynGeneratorTraverser(tree_g).postorder()
tag = tree[1].internal
contentList = tree_g[1].dict

#Analyzing semantics

RequiredTags = {'<html>':False,'<head>':False,'<body>':False} #required tag check
for t in tag:
    checkRequiredTags(t,RequiredTags)
for r in RequiredTags:
    if RequiredTags[r] == False:
        print("Codezyn Error: Required Tag " + r + " missing.")
        exit()

for t in tag: #CSS Properties check
    checkCSS(t)
        
validIdentifiers = [] #matching generator IDs with Tag IDs
for t in tag:
    getValidTagIdentifiers(t)

for key in contentList:
    if not key in validIdentifiers:
        print("Codezyn Error: Invalid Tag Identifier '" + key + "' in generator file.")
        exit()
        
#Generating output
forCSS = argv[1].split("/");
fileCSS = open(argv[1] + ".css",'w')
fileHTML = open(argv[1] + ".html",'w')
for t in tag:
    generateCode(t)
fileCSS.close()
fileHTML.close()
print "Codezyn Message: See " + argv[1] + ".html for target code."
