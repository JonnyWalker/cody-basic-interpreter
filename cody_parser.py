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

    def rest(self):
        return self.string[self.pos :]

    def advance(self):
        assert not self.is_eol()
        self.pos += 1

    def is_eol(self):
        return len(self.string) <= self.pos

    def expect(self, s: str, skip_ws=True):
        for c in s:
            assert self.peek() == c
            self.advance()
        if skip_ws:
            self.skip_whitespace()

    def skip_whitespace(self):
        while self.peek().isspace():
            self.advance()

    def parse(self, string=None, list=False, rel_op=False, ignore_tail=False):
        if string is not None:
            self.pos = 0
            self.string = string
            self.skip_whitespace()
        else:
            assert self.pos is not None and self.string is not None
        if list:
            node = self.parse_list(rel_op=rel_op)
        else:
            node = self.parse_expr(rel_op=rel_op)
        if not ignore_tail and self.peek():
            raise Exception("expected end of input")
        return node

    def parse_list(self, rel_op=False):
        nodes = []
        if self.peek():
            nodes.append(self.parse_expr(rel_op=rel_op))
            while self.peek() == ",":
                self.advance()
                self.skip_whitespace()
                node = self.parse_expr(rel_op=rel_op)
                nodes.append(node)
        return nodes

    def parse_expr(self, rel_op=False):
        if rel_op:
            return self.parse_rel_op()
        else:
            return self.parse_term()

    def parse_rel_op(self):
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
            self.skip_whitespace()
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
            self.skip_whitespace()
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
            self.skip_whitespace()
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

        self.skip_whitespace()
        expr = self.parse_unary()
        node = ASTNode(op_type)
        node.expr = expr
        return node

    def parse_primary(self):
        c = self.peek()
        if c == '"':
            return self.parse_string_literal()
        elif c == "(":
            self.advance()
            self.skip_whitespace()
            node = self.parse_expr()
            self.expect(")")
            return node
        elif c.isdigit():
            return self.parse_integer_literal()
        elif c.isalpha():
            return self.parse_variable_or_builtin()
        else:
            raise Exception("parse error")

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
        self.skip_whitespace()
        return node

    def parse_string_literal(self):
        self.expect('"', skip_ws=False)
        literal = ""
        while True:
            c = self.peek()
            self.advance()
            if c == '"':
                break
            else:
                literal += c
        assert len(literal) <= 255
        node = ASTNode(ASTTypes.StringLiteral)
        node.literal = literal
        self.skip_whitespace()
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
        self.skip_whitespace()

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
            param_mode = "none"  # no arrays for string vars
            node = ASTNode(ASTTypes.StringVariable)
            name = name[0]  # TODO: maybe the name should include the $
        else:
            raise NotImplementedError(f"unknown built-in {name}")
        node.name = name

        # check if variable/builtin can have parameters
        if param_mode != "none":
            if self.peek() == "(":
                self.advance()
                self.skip_whitespace()
                if self.peek() == ")":
                    expressions = []
                else:
                    expressions = self.parse_list()
                self.expect(")")

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

    def parse_command(self, command: str, line_number: bool = True) -> Command:
        source = command
        command = command.strip()

        # (1) split line number if present
        if line_number:
            for i, c in enumerate(command):
                if not c.isdigit():
                    break
        else:
            i = 0
        if i > 0:
            line_number = int(command[:i])
            assert 0 <= line_number < 65535
            command = command[i:].strip()
        else:
            line_number = None

        # (2) parse command type
        for command_type in CommandTypes:
            if command_type.valid_prefix and command.startswith(command_type.name):
                other = command[len(command_type.name) :].strip()
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
                    f"expected end of line after command {c.command_type.name}, but was '{other}'"
                )
        elif c.command_type == CommandTypes.ASSIGNMENT:
            c.lvalue = self.parse(other, ignore_tail=True)
            assert c.lvalue.ast_type in (
                ASTTypes.IntegerVariable,
                ASTTypes.StringVariable,
                ASTTypes.ArrayExpression,
            )
            self.expect("=")
            c.rvalue = self.parse()
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
            CommandTypes.READ,
        ):
            c.expressions = self.parse(other, list=True)
            assert len(c.expressions) >= 1
        elif c.command_type == CommandTypes.DATA:
            c.expressions = self.parse(other, list=True)
            assert len(c.expressions) >= 1
            for expr in c.expressions:
                assert expr.ast_type == ASTTypes.IntegerLiteral or (
                    expr.ast_type == ASTTypes.UnaryMinus
                    and expr.expr.ast_type == ASTTypes.IntegerLiteral
                )
        elif c.command_type == CommandTypes.IF:
            c.condition = self.parse(other, rel_op=True, ignore_tail=True)
            assert c.condition.ast_type in (
                ASTTypes.Equal,
                ASTTypes.NotEqual,
                ASTTypes.Less,
                ASTTypes.LessEqual,
                ASTTypes.Greater,
                ASTTypes.GreaterEqual,
            )
            # TODO: check that for string comparisons the left side of the rel op must be a var
            self.expect("THEN")
            assert not self.is_eol()
            c.command = self.parse_command(self.rest(), line_number=False)
        elif c.command_type == CommandTypes.FOR:
            c.loop_variable = self.parse(other, ignore_tail=True)
            assert c.loop_variable.ast_type in (
                ASTTypes.IntegerVariable,
                ASTTypes.StringVariable,
                ASTTypes.ArrayExpression,
            )
            self.expect("=")
            c.initial = self.parse(ignore_tail=True)
            self.expect("TO")
            c.limit = self.parse()
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
