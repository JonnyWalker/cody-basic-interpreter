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
commands = [
    "REM",
    "POKE",
    "GOSUB",
    "PRINT",
    "IF",
    "END",
    "INPUT",
    "GOTO",
    "NEXT",
    "FOR",
    "RETURN",
]


class Command:
    def __init__(self, command_type):
        self.line_number = None
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
            return node  # TODO fix invalid bounds (-32768 to 32767)

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

    def parse_statement(self, command):
        # (1) parse command type
        for command_type in commands:
            if command.startswith(command_type):
                rest = command[len(command_type) :]
                break
        else:  # special parsing case for assignments
            if "=" in command:
                command_type = "ASSIGNMENT"
                rest = command
            else:
                raise NotImplementedError("error! unknown command: " + command)
        c = Command(command_type)

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
        if c.command_type in ("REM", "NEXT", "RETURN", "END"):
            pass
        elif c.command_type == "ASSIGNMENT":
            name, expression = other.split("=", 1)
            c.lvalue = self.parse(name)
            c.rvalue = self.parse(expression)
        elif c.command_type == "POKE":
            pass  # TODO: parse Expression
        elif c.command_type == "GOSUB":
            c.expression = self.parse(other)
        elif c.command_type == "PRINT":
            c.expression = self.parse(other)
            if other.endswith(";"):  # page 249, semicolon = no new line
                c.no_new_line = True
            else:
                c.no_new_line = False
        elif c.command_type == "IF":
            condition, statement = other.split("THEN", 1)
            c.condition = self.parse(condition)
            c.command = self.parse_statement(statement)
        elif c.command_type == "INPUT":
            c.expression = self.parse(other)
        elif c.command_type == "GOTO":
            c.expression = self.parse(other)
        elif c.command_type == "FOR":
            assignment, limit = other.split("TO", 1)
            c.assignment = self.parse_statement(assignment)
            c.limit = self.parse(limit)
        else:
            raise NotImplementedError(f"unknown command type {c.command_type}")
        return c

    def parse_line(self, line):
        # (0) split at first space, which must be after the line number
        line_number, command = line.split(" ", 1)
        line_number = int(line_number)
        cmd = self.parse_statement(command)
        cmd.line_number = line_number
        return cmd

    def parse_program(self, lines):
        parsed_commands = []
        for line in lines:
            c = self.parse_line(line)
            parsed_commands.append(c)
        return parsed_commands

    def parse_file(self, filename):
        with open(filename) as f:
            lines = f.readlines()
        return self.parse_program(lines)

    def parse_string(self, code: str):
        lines = code.splitlines()
        return self.parse_program(lines)
