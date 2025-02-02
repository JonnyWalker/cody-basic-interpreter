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
    Greater = 11
    Less = 12
    Equal = 13


# TODO: also use an enum
commands = ["REM", "POKE", "GOSUB", "PRINT", "IF", "END",
            "INPUT", "GOTO", "NEXT", "FOR", "RETURN"]

class Command:
    def __init__(self, line_number, command_type):
        self.line_number = line_number
        self.command_type = command_type

class ASTNode:
    def __init__(self, ast_type):
        self.ast_type = ast_type

class CodyBasicParser:
    def peek(self):
        if self.is_eol():
            return ""
        return self.string[self.pos]
    
    def advance(self):
        self.pos += 1

    def is_eol(self):
        return len(self.string) == self.pos
    
    def parse(self, string):
        self.pos = 0
        # TODO: remove spaces
        self.string = string    
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
        left = self.parse_term()
        if "<" in self.peek():
            self.advance()
            right = self.parse_term()
            node = ASTNode(ASTTypes.Less)
            node.left = left
            node.right = right
            return node
        elif ">" in self.peek():
            self.advance()
            right = self.parse_term()
            node = ASTNode(ASTTypes.Greater)
            node.left = left
            node.right = right
            return node
        elif "=" in self.peek():
            self.advance()
            right = self.parse_term()
            node = ASTNode(ASTTypes.Equal)
            node.left = left
            node.right = right
            return node
        return left

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


    def parse_command(self, line):
        # (0) split at first space, which musst be after the line numer
        splitted = line.split(" ", 1)
        line_number = int(splitted[0])
        
        # (1) parse command type
        is_assignment = True
        for command in commands:
            if splitted[1].startswith(command):
                is_assignment = False
                command_type = command
                rest = splitted[1][len(command):]
                break
        if is_assignment: # special parsing case for assignments 
            if "=" in splitted[1]:
                command_type = "ASSIGNMENT"
                rest = splitted[1]
            else:
                raise NotImplementedError("error! unknown command:"+splitted[1])
        c = Command(line_number, command_type)

        # (2) remove spaces from rest, except in string literal
        other = ""
        inside_string_literal = False
        for char in rest:
            if char == '"':
                inside_string_literal = not inside_string_literal
            elif char == " ":
                if not inside_string_literal:
                    continue
            other += char

        # (3) parse other parts
        if c.command_type == "ASSIGNMENT":
            name, expression = other.split("=")
            c.lvalue = self.parse(name)  
            c.rvalue = self.parse(expression)
        elif c.command_type == "POKE":
            pass # TODO: parse Expression
        elif c.command_type == "GOSUB":
            c.expression = self.parse(other)
        elif c.command_type == "PRINT":
            c.expression = self.parse(other)
            if ";" == other[-1]: # page 249, semicolon = no new line
                c.no_new_line = True
            else:
                c.no_new_line = False
        elif c.command_type == "IF":
            condition, _ = other.split("THEN")
            _, statement = line.split("THEN", 1)
            c.condition = self.parse(condition)
             # FIXME: remove fake line nubmer hack
            c.command = self.parse_command("000"+ statement)
        elif c.command_type == "INPUT":
            c.expression = self.parse(other)
        elif c.command_type == "GOTO":
            c.expression = self.parse(other)
        elif c.command_type == "NEXT":
            pass
        elif c.command_type == "FOR":
            pass
        elif c.command_type == "RETURN":
            pass
        elif c.command_type == "END":
            pass    
        return c

    def parse_program(self, code):
        parsed_commands = []
        for command in code:
            c = self.parse_command(command)
            parsed_commands.append(c) 
        return parsed_commands   

    def parse_file(self, filename):
        code = []
        with open(filename) as f:
            for line in f:
                code.append(line)
        return self.parse_program(code)
                