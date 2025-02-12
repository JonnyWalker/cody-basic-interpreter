from enum import Enum, auto, unique
from typing import Optional


@unique
class ASTTypes(Enum):
    IntegerLiteral = auto()
    StringLiteral = auto()
    StringVariable = auto()
    IntegerVariable = auto()
    ArrayExpression = auto()
    UnaryMinus = auto()
    BinaryAdd = auto()
    BinarySub = auto()
    BinaryMul = auto()
    BinaryDiv = auto()
    Equal = auto()
    NotEqual = auto()
    Less = auto()
    LessEqual = auto()
    Greater = auto()
    GreaterEqual = auto()


# TODO: also use an enum
commands = [
    "REM",
    "GOSUB",
    "PRINT",
    "IF",
    "END",
    "INPUT",
    "GOTO",
    "NEXT",
    "FOR",
    "RETURN",
    "OPEN",
    "CLOSE",
    "DATA",
    "READ",
    "RESTORE",
    "POKE",
    "SYS",
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

    def parse(self, string, list=False, ignore_tail=False):
        self.pos = 0
        self.string = string
        if list:
            node = self.parse_list()
        else:
            node = self.parse_expr()
        if not ignore_tail and self.peek():
            raise Exception("expected end of input")
        return node

    def parse_list(self):
        nodes = []
        if self.peek():
            nodes.append(self.parse_expr())
            while "," in self.peek():
                self.advance()
                node = self.parse_expr()
                nodes.append(node)
        return nodes

    def parse_expr(self):
        return self.parse_comparison()

    def parse_comparison(self):
        ops = {
            "=": ASTTypes.Equal,
            "<>": ASTTypes.NotEqual,
            "<": ASTTypes.Less,
            "<=": ASTTypes.LessEqual,
            ">": ASTTypes.Greater,
            ">=": ASTTypes.GreaterEqual,
        }
        left = self.parse_term()
        while op_type := self.find_op(ops):
            right = self.parse_term()
            node = ASTNode(op_type)
            node.left = left
            node.right = right
            left = node
        return left

    def parse_term(self):
        ops = {
            "+": ASTTypes.BinaryAdd,
            "-": ASTTypes.BinarySub,
        }
        left = self.parse_factor()
        while op_type := self.find_op(ops):
            right = self.parse_factor()
            node = ASTNode(op_type)
            node.left = left
            node.right = right
            left = node
        return left

    def parse_factor(self):
        ops = {
            "*": ASTTypes.BinaryMul,
            "/": ASTTypes.BinaryDiv,
        }

        left = self.parse_unary()
        while op_type := self.find_op(ops):
            right = self.parse_unary()
            node = ASTNode(op_type)
            node.left = left
            node.right = right
            left = node
        return left

    def parse_unary(self):
        ops = {
            "-": ASTTypes.UnaryMinus,
        }

        op_type = self.find_op(ops)
        if not op_type:
            return self.parse_primary()

        expr = self.parse_unary()
        node = ASTNode(op_type)
        node.expr = expr
        return node

    def parse_primary(self):
        c = self.peek()
        if c == '"':
            node = self.parse_string_literal()
        elif c == "(":
            self.advance()
            node = self.parse_expr()
            assert self.peek() == ")"
            self.advance()
        elif c.isdigit():
            node = self.parse_integer_literal()
        elif c.isalpha():
            node = self.parse_variable()
        else:
            raise Exception("parse error")
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
        if -32768 <= node.value <= 32767:
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
            # book page 253:
            # "Cody BASIC also has 26 string variables A$ through Z$"
            self.advance()
            node = ASTNode(ASTTypes.StringVariable)
            node.name = name
        elif self.peek().isalpha():
            # musst be a built-in like MOD(8,5)
            raise NotImplementedError("built-in not implemeted yet")
        else:
            # book page 252:
            # "Number Variables are represented by a letter between A and Z"
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

    def find_op(self, ops: dict[str, ASTTypes]) -> Optional[ASTTypes]:
        """
        Find the longest matching key in "ops" and return its value.
        """
        initial_pos = self.pos
        valid_tokens = list(ops.keys())
        last_valid_token = None
        op = ""
        while True:
            next_char = self.peek()
            if not next_char:
                break  # eol
            op += next_char
            self.advance()

            valid_tokens = [t for t in valid_tokens if t.startswith(op)]
            if not valid_tokens:
                break
            elif op in ops:
                last_valid_token = op

        self.pos = initial_pos + (len(last_valid_token) if last_valid_token else 0)
        return ops[last_valid_token] if last_valid_token else None

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
        if c.command_type == "REM":
            pass  # ignore line
        elif c.command_type in ("NEXT", "RETURN", "END", "CLOSE", "RESTORE"):
            if other:
                raise Exception("expected end of line")
        elif c.command_type == "ASSIGNMENT":
            ast = self.parse(other)
            assert ast.ast_type == ASTTypes.Equal
            c.lvalue, c.rvalue = ast.left, ast.right
        elif c.command_type in ("GOTO", "GOSUB"):
            c.expression = self.parse(other)
        elif c.command_type == "PRINT":
            c.expressions = self.parse(other, list=True, ignore_tail=True)
            if self.peek() == ";":  # page 249, semicolon = no new line
                self.advance()
                c.no_new_line = True
            else:
                c.no_new_line = False
            if self.peek():
                raise Exception("expected end of line")
        elif c.command_type in ("INPUT", "DATA", "READ"):
            c.expressions = self.parse(other, list=True)
            assert len(c.expressions) >= 1
        elif c.command_type == "IF":
            condition, statement = other.split("THEN", 1)
            c.condition = self.parse(condition)
            c.command = self.parse_statement(statement)
        elif c.command_type == "FOR":
            assignment, limit = other.split("TO", 1)
            c.assignment = self.parse_statement(assignment)
            c.limit = self.parse(limit)
        elif c.command_type == "OPEN":
            c.uart, c.bit_rate = self.parse(other, list=True)
        elif c.command_type == "POKE":
            c.address, c.expression = self.parse(other, list=True)
        elif c.command_type == "SYS":
            c.address = self.parse(other)
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
            line = line.strip()
            if not line:
                continue  # skip empty lines
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
