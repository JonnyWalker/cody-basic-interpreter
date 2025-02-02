from enum import Enum

class ASTTypes(Enum):
    IntegerLiteral = 1
    StringLiteral = 2
    BinaryAdd = 3
    BinarySub = 4
    StringVariable = 5
    IntegerVariable = 6
    ExpressionList = 7
    ArrayExpression = 8
    BinaryMul = 9
    BinaryDiv = 10


# TODO: also use an enum
commands = ["REM", "POKE", "GOSUB", "PRINT", "IF", 
            "INPUT", "GOTO", "NEXT", "FOR", "RETURN"]

class Command:
    def __init__(self, line_number, command_type):
        self.line_number = line_number
        self.command_type = command_type

class ASTNode:
    def __init__(self, ast_type):
        self.ast_type = ast_type

class ExpressionParser:
    def __init__(self, string):
        self.pos = 0
        # TODO: remove spaces
        self.string = string

    def peek(self):
        if self.is_eol():
            return ""
        return self.string[self.pos]
    
    def advance(self):
        self.pos += 1

    def is_eol(self):
        return len(self.string) == self.pos
    
    def parse(self):
        node = self.parse_list()
        return node
    
    def parse_list(self):
        node = self.parse_equality()
        if "," in self.peek():
            expr_list = [node]
            while "," in self.peek():
                self.advance()        
                node = self.parse_equality()
                expr_list.append(node)
            node = ASTNode(ASTTypes.ExpressionList)
            node.expr_list = expr_list
        return node

    def parse_equality(self):
        return self.parse_comparision()    

    def parse_comparision(self):
        return self.parse_term()

    def parse_term(self):
        left = self.parse_factor()
        if "+" in self.peek():
            self.advance()
            right = self.parse_factor()
            node = ASTNode(ASTTypes.BinaryAdd)
            node.left = left
            node.right = right
            return node
        elif "-" in self.peek():
            self.advance()
            right = self.parse_factor()
            node = ASTNode(ASTTypes.BinarySub)
            node.left = left
            node.right = right
            return node
        return left

    def parse_factor(self):
        left = self.parse_unary()
        if "*" in self.peek():
            self.advance()
            right = self.parse_unary()
            node = ASTNode(ASTTypes.BinaryMul)
            node.left = left
            node.right = right
            return node
        elif "/" in self.peek():
            self.advance()
            right = self.parse_unary()
            node = ASTNode(ASTTypes.BinaryDiv)
            node.left = left
            node.right = right
            return node
        return left   

    def parse_unary(self):
        return self.parse_primary()
    
    def parse_primary(self):
        if '"' == self.peek():
            node = self.parse_string_literal()
        elif self.peek().isdigit():
            node = self.parse_integer_literal()
        elif self.peek().isalpha():
            node = self.parse_variable() 
        else:
            print("parse error")
        return node

    def parse_integer_literal(self):
        literal = self.peek()
        while True:
            self.advance()
            if self.peek().isdigit():
                literal += self.peek()
            else:
                break
        node = ASTNode(ASTTypes.IntegerLiteral)
        node.value = int(literal)
        if node.value >= -32768 and node.value <= 32767:
            return node
        else:
            return node # TODO fix invalid bounds (-32768 to 32767)            

    def parse_string_literal(self):
        assert '"' == self.peek()
        literal = ""
        while True:
            self.advance()
            c = self.peek()
            if c == '"':
                break
            else:
                literal += c
        self.advance()
        node = ASTNode(ASTTypes.StringLiteral)
        node.literal = literal
        return node
    
    def parse_variable(self):
        name = self.peek()
        self.advance()
        if "$" == self.peek():
            self.advance()
            node = ASTNode(ASTTypes.StringVariable)
            node.name = name
        else:
            node = ASTNode(ASTTypes.IntegerVariable)
            node.name = name

        if "(" == self.peek():
            index = ""
            self.advance()
            while ")" != self.peek():
                index += self.peek()
                self.advance()
            self.advance()
            subnode = node
            node = ASTNode(ASTTypes.ArrayExpression)
            node.subnode = subnode
            node.index = int(index)
        return node           


def parse_command(line):
    # TODO: This will break some day. Replace with better parsing
    splitted = line.split()
    line_number = int(splitted[0])
    command = splitted[1]
    # bugfix for the broken split approach: readd spaces :-D
    if len(splitted) > 2:
        rest = splitted[2]
        if len(splitted) > 3:
            for s in splitted[3:]:
                rest += " "+s 
    
    # (1) parse command type
    if command not in commands: # special parsing case
        if "=" in command:
            command_type = "ASSIGNMENT"
        else:
            print("error! unknown command:"+command)
    else:
        command_type = command
    c = Command(line_number, command_type)

    # (2) parse other parts
    if c.command_type == "ASSIGNMENT":
        name, expression = splitted[1].split("=")  
        expr_parse = ExpressionParser(expression)
        c.rvalue = expr_parse.parse()
        expr_parse = ExpressionParser(name)
        c.lvalue = expr_parse.parse()
    elif c.command_type == "POKE":
        pass # TODO: parse Expression
    elif c.command_type == "GOSUB":
        pass
    elif c.command_type == "PRINT":
        expr_parse = ExpressionParser(rest)
        c.expression = expr_parse.parse()
        if ";" == rest[-1]: # page 249, semicolon = no new line
            c.no_new_line = True
        else:
            c.no_new_line = False
    elif c.command_type == "IF":
        pass
    elif c.command_type == "INPUT":
        expr_parse = ExpressionParser(rest)
        c.expression = expr_parse.parse()
    elif c.command_type == "GOTO":
        pass
    elif c.command_type == "NEXT":
        pass
    elif c.command_type == "FOR":
        pass
    elif c.command_type == "RETURN":
        pass
    return c

def parse_program(code):
    parsed_commands = []
    for command in code:
        c = parse_command(command)
        parsed_commands.append(c) 
    return parsed_commands   

def parse_file(filename):
    code = []
    with open(filename) as f:
        for line in f:
            code.append(c)
    return parse_program(code)
            