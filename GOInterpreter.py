import collections
import sys
from dataclasses import dataclass
from token import NAME, NUMBER
import lark
import rich

@dataclass
class Variable:
  type: str
  value: int | None

# version 4 [nested functions]
grammar = r"""
program:     definition* | function* | call* | start
function:    "func" NAME "(" ")" "{" statement* "}" end
internfunction: NAME ":=" "func" "(" ")" "{" statement* "}" end 
end:
?statement:  definition | attribution | directattribution | print | call | internfunction
start:       "main" "(" ")" "{" statement* "}" end
definition:  "var" NAME "inter"
attribution: NAME "=" NUMBER 
directattribution: NAME ":=" NUMBER
print:       "Println" "(" NAME ")"
call:        NAME "()"

NAME:   /\w+/
NUMBER: /\d+/ | /\w+/
%ignore /[ \t\n\r]+/
"""

program = """

func f() {
  var c inter
  c = 1
  Println(c)
}
func main() {
  var a inter
	a = 10
  b := 20
  a = b
  Println(a)
  Println(b)
  f()
  f()
}
"""

parser = lark.Lark(grammar, start='program')
tree = parser.parse(program)
rich.print(tree)
symbol_table = collections.ChainMap({'scope': 'global'})
global_functions = {}
not_used_table = {}

class Walker:
  def start(self):
    symbol_table.maps.insert(0, {'scope': 'main()'})

  def internfunction(self):
    pass 

  def function(self, NAME):
    if NAME not in symbol_table.maps[0]:
      global_functions[NAME] = None
    else: 
      rich.print('[red]error: redefined function', NAME)

  def call(self, NAME): 
    if NAME in symbol_table:
      symbol_table.maps.insert(0, {'scope': NAME+'()'})
    else:
      rich.print('[red]error: unknown function', NAME)
  
  def end(self):
    if len(not_used_table) > 0:
      rich.print('[red]error: unused variable(s)', not_used_table)
      sys.exit(1)
    rich.print(symbol_table)
    symbol_table.maps.pop(0)

  def definition(self, NAME):
    symbol_table[NAME] = Variable('inter', None)
    not_used_table[NAME] = None

  def directattribution(self, NAME, NUMBER):
    if NUMBER.isdigit():
      symbol_table[NAME] = Variable('inter', int(NUMBER))
      not_used_table[NAME] = None
    elif NUMBER in symbol_table: 
      symbol_table[NAME] = Variable('inter', symbol_table[NUMBER].value)
      not_used_table[NAME] = None
      if NUMBER in not_used_table:
        not_used_table.pop(NUMBER)
    else: 
      rich.print('[red]error: unknown variable', NUMBER)

  def attribution(self, NAME, NUMBER):
    if NAME in symbol_table:
      if NUMBER.isdigit():
        symbol_table[NAME] = Variable('inter', int(NUMBER))
      elif NUMBER in symbol_table: 
        symbol_table[NAME] = Variable('inter', symbol_table[NUMBER].value)
        if NUMBER in not_used_table:
          not_used_table.pop(NUMBER)
      else: 
        rich.print('[red]error: unknown variable', NUMBER)
    else: 
      rich.print('[red]error: unknown variable', NAME)
    
  def print(self, NAME):
    if NAME in symbol_table:
      print(symbol_table[NAME].value)
      not_used_table.pop(NAME)
    else:
      rich.print('[red]error: unknown variable', NAME)

  def visit(self, node):
    vals = [t.value for t in node.children if type(t) is lark.Token]
    if hasattr(self, node.data):
        getattr(self, node.data)(*vals)
    for child in node.children:
      if type(child) is lark.Tree:
        self.visit(child)

Walker().visit(tree)
