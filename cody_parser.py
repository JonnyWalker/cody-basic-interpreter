from enum import Enum, auto, unique
from typing import Optional, Iterable
from cody_util import twos_complement


@unique
class ASTTypes(Enum):
    BuiltInCall = auto()
    BuiltInVariable = auto()
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


@unique
class CommandTypes(Enum):
    ASSIGNMENT = auto()
    EMPTY = auto()
    REM = auto()
    GOSUB = auto()
    PRINT = auto()
    IF = auto()
    END = auto()
    INPUT = auto()
    GOTO = auto()
    NEXT = auto()
    FOR = auto()
    RETURN = auto()
    OPEN = auto()
    CLOSE = auto()
    DATA = auto()
    READ = auto()
    RESTORE = auto()
    POKE = auto()
    SYS = auto()
    NEW = auto()
    LOAD = auto()
    SAVE = auto()
    RUN = auto()
    LIST = auto()

    @property
    def valid_prefix(self) -> bool:
        return self not in (CommandTypes.ASSIGNMENT, CommandTypes.EMPTY)


builtin_functions = [
    "ABS",
    "ASC",
    "AND",
    "AT",
    "CHR$",
    "LEN",
    "MOD",
    "NOT",
    "OR",
    "PEEK",
    "RND",
    "SQR",
    "STR$",
    "SUB$",
    "TAB",
    "VAL",
    "XOR",
]

builtin_vars = [
    "TI",
]


class Command:
    def __init__(
        self,
        command_type: CommandTypes,
        line_number: Optional[int] = None,
        source: Optional[str] = None,
    ):
        self.command_type = command_type
        self.line_number = line_number
        self.source = source


class ASTNode:
    def __init__(self, ast_type: ASTTypes):
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
            node = self.parse_variable_or_builtin()
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
        node.value = twos_complement(int(literal))
        return node

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
        assert len(literal) <= 255
        self.advance()
        node = ASTNode(ASTTypes.StringLiteral)
        node.literal = literal
        return node

    def parse_variable_or_builtin(self):
        assert self.peek().isalpha()
        name = ""

        # var name
        while (c := self.peek()).isalpha():
            name += c
            self.advance()
        # string suffix
        if c == "$":
            name += c
            self.advance()

        if name in builtin_vars:
            param_mode = "none"
            node = ASTNode(ASTTypes.BuiltInVariable)
        elif name in builtin_functions:
            param_mode = "any"
            node = ASTNode(ASTTypes.BuiltInCall)
        elif len(name) == 1:
            # book page 252:
            # "Number Variables are represented by a letter between A and Z"
            param_mode = "array"
            node = ASTNode(ASTTypes.IntegerVariable)
        elif len(name) == 2 and name[1] == "$":
            # book page 253:
            # "Cody BASIC also has 26 string variables A$ through Z$"
            param_mode = "array"
            node = ASTNode(ASTTypes.StringVariable)
            name = name[0]  # TODO: maybe the name should include the $
        else:
            raise NotImplementedError(f"unknown built-in {name}")
        node.name = name

        # check if variable/builtin can have parameters
        if param_mode != "none":
            if self.peek() == "(":
                self.advance()
                if self.peek() == ")":
                    expressions = []
                else:
                    expressions = self.parse_list()
                assert self.peek() == ")"
                self.advance()

                if param_mode == "array":
                    assert len(expressions) == 1
                    subnode = node
                    node = ASTNode(ASTTypes.ArrayExpression)
                    node.subnode = subnode
                    node.index = expressions[0]
                else:
                    # built-in functions can take any number of parameters
                    assert param_mode == "any"
                    node.expressions = expressions
            elif param_mode == "any":
                # builtin functions require parentheses
                raise ValueError(
                    f"built-in {param_mode} requires arguments but none were given"
                )
            else:
                assert param_mode == "array"  # parameters are optional

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

    def strip_whitespace(self, s: str) -> str:
        stripped = ""
        inside_string_literal = False
        for char in s:
            if char == '"':
                inside_string_literal = not inside_string_literal
            elif char == " ":
                if not inside_string_literal:
                    continue
            stripped += char
        return stripped

    def parse_command(self, command: str) -> Command:
        source = command

        # (0) remove spaces, except in string literal
        command = self.strip_whitespace(command)

        # (1) split line number if present
        for i, c in enumerate(command):
            if not c.isdigit():
                break
        if i > 0:
            line_number = int(command[:i])
            command = command[i:]
        else:
            line_number = None

        # (2) parse command type
        for command_type in CommandTypes:
            if command_type.valid_prefix and command.startswith(command_type.name):
                other = command[len(command_type.name) :]
                break
        else:  # special parsing case for empty string and assignments
            if not command:
                command_type = CommandTypes.EMPTY
                other = command
            #  just a heuristic, might break with "=" in string literal
            elif "=" in command:
                command_type = CommandTypes.ASSIGNMENT
                other = command
            else:
                raise NotImplementedError("error! unknown command: " + source)
        c = Command(command_type, line_number, source)

        # (3) parse other parts
        if c.command_type == CommandTypes.REM:
            pass  # ignore line
        elif c.command_type in (
            CommandTypes.EMPTY,
            CommandTypes.NEXT,
            CommandTypes.RETURN,
            CommandTypes.END,
            CommandTypes.CLOSE,
            CommandTypes.RESTORE,
            CommandTypes.NEW,
            CommandTypes.RUN,
        ):
            if other:
                raise Exception(
                    f"expected end of line after command {c.command_type.name}, but was {other}"
                )
        elif c.command_type == CommandTypes.ASSIGNMENT:
            ast = self.parse(other)
            assert ast.ast_type == ASTTypes.Equal
            c.lvalue, c.rvalue = ast.left, ast.right
        elif c.command_type in (CommandTypes.GOTO, CommandTypes.GOSUB):
            c.expression = self.parse(other)
        elif c.command_type == CommandTypes.PRINT:
            c.expressions = self.parse(other, list=True, ignore_tail=True)
            if self.peek() == ";":  # page 249, semicolon = no new line
                self.advance()
                c.no_new_line = True
            else:
                c.no_new_line = False
            if self.peek():
                raise Exception("expected end of line")
        elif c.command_type in (
            CommandTypes.INPUT,
            CommandTypes.DATA,
            CommandTypes.READ,
        ):
            c.expressions = self.parse(other, list=True)
            assert len(c.expressions) >= 1
        elif c.command_type == CommandTypes.IF:
            condition, statement = other.split("THEN", 1)
            c.condition = self.parse(condition)
            c.command = self.parse_command(statement)
        elif c.command_type == CommandTypes.FOR:
            assignment, limit = other.split("TO", 1)
            c.assignment = self.parse_command(assignment)
            c.limit = self.parse(limit)
        elif c.command_type == CommandTypes.OPEN:
            c.uart, c.bit_rate = self.parse(other, list=True)
        elif c.command_type == CommandTypes.POKE:
            c.address, c.expression = self.parse(other, list=True)
        elif c.command_type == CommandTypes.SYS:
            c.address = self.parse(other)
        elif c.command_type == CommandTypes.LIST:
            exprs = self.parse(other, list=True)
            assert len(exprs) <= 2
            c.start = exprs[0] if len(exprs) >= 1 else None
            c.end = exprs[1] if len(exprs) >= 2 else None
        elif c.command_type == CommandTypes.LOAD:
            c.uart, c.mode = self.parse(other, list=True)
        elif c.command_type == CommandTypes.SAVE:
            c.uart = self.parse(other)
        else:
            raise NotImplementedError(
                f"command type {c.command_type.name} not implemented"
            )
        return c

    def parse_lines(self, lines: Iterable[str]) -> list[Command]:
        parsed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue  # skip empty lines
            c = self.parse_command(line)
            parsed.append(c)
        return parsed

    def parse_file(self, filename: str) -> list[Command]:
        with open(filename) as f:
            lines = f.readlines()
        return self.parse_lines(lines)

    def parse_string(self, code: str) -> list[Command]:
        lines = code.splitlines()
        return self.parse_lines(lines)
