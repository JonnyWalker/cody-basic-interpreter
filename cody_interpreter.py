from cody_parser import ASTTypes
from abc import ABC, abstractmethod
from typing import Optional, Iterable
from cody_util import twos_complement
import time
import random
import math


class IO(ABC):
    @abstractmethod
    def print(self, value): ...

    @abstractmethod
    def println(self): ...

    @abstractmethod
    def input(self) -> str: ...


class Interpreter:
    def __init__(self, io: Optional[IO] = None):
        self.io = io if io is not None else StdIO()
        self.reset()

    def compute_target(self, node):
        if node.ast_type == ASTTypes.ArrayExpression:
            index = node.index
            target = node.subnode
        elif node.ast_type in (
            ASTTypes.IntegerVariable,
            ASTTypes.StringVariable,
            ASTTypes.BuiltInVariable,
        ):
            index = 0
            target = node
        else:
            raise ValueError(f"cannot read/write to node {node.ast_type}")
        return index, target

    def add_value(self, target, value, index, convert_int=False):
        if target.ast_type == ASTTypes.IntegerVariable:
            if convert_int:
                value = int(value)
            else:
                assert isinstance(value, int)
            self.int_arrays.setdefault(target.name, {})[index] = twos_complement(value)
        elif target.ast_type == ASTTypes.StringVariable:
            # string arrays not supported
            assert isinstance(value, str) and len(value) <= 255 and index == 0
            self.string_arrays.setdefault(target.name, {})[index] = value
        else:
            raise ValueError(f"cannot write to node {target.ast_type}")

    def eval(self, node):
        if node.ast_type == ASTTypes.Equal:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert type(left) == type(right)
            return left == right
        elif node.ast_type == ASTTypes.NotEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert type(left) == type(right)
            return left != right
        elif node.ast_type == ASTTypes.Less:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert type(left) == type(right)
            return left < right
        elif node.ast_type == ASTTypes.LessEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert type(left) == type(right)
            return left <= right
        elif node.ast_type == ASTTypes.Greater:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert type(left) == type(right)
            return left > right
        elif node.ast_type == ASTTypes.GreaterEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert type(left) == type(right)
            return left >= right
        elif node.ast_type == ASTTypes.BinaryAdd:
            left = self.eval(node.left)
            right = self.eval(node.right)
            if isinstance(left, int) and isinstance(right, int):
                return twos_complement(left + right)
            else:
                value = f"{left}{right}"
                assert len(value) <= 255
                return value
        elif node.ast_type == ASTTypes.BinarySub:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return twos_complement(left - right)
        elif node.ast_type == ASTTypes.BinaryMul:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return twos_complement(left * right)
        elif node.ast_type == ASTTypes.BinaryDiv:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return twos_complement(left // right)  # integer div
        elif node.ast_type == ASTTypes.UnaryMinus:
            expr = self.eval(node.expr)
            return twos_complement(-expr)
        elif node.ast_type == ASTTypes.StringLiteral:
            assert isinstance(node.literal, str) and len(node.literal) <= 255
            return node.literal
        elif node.ast_type == ASTTypes.IntegerLiteral:
            return twos_complement(node.value)
        elif node.ast_type in (
            ASTTypes.IntegerVariable,
            ASTTypes.StringVariable,
            ASTTypes.ArrayExpression,
        ):
            index, target = self.compute_target(node)
            if target.ast_type == ASTTypes.IntegerVariable:
                array = self.int_arrays.setdefault(target.name, {})
                return twos_complement(array.setdefault(index, 0))
            elif target.ast_type == ASTTypes.StringVariable:
                assert index == 0  # string arrays not supported
                array = self.string_arrays.setdefault(target.name, {})
                value = array.setdefault(index, "")
                assert isinstance(value, str) and len(value) <= 255
                return value
            else:
                raise AssertionError
        elif node.ast_type == ASTTypes.BuiltInVariable:
            return self.eval_builtin_var(node.name)
        elif node.ast_type == ASTTypes.BuiltInCall:
            return self.eval_builtin_function(node.name, node.expressions)
        else:
            raise NotImplementedError(f"ast type {node.ast_type} not implemented")

    def eval_builtin_var(self, name):
        if name == "TI":
            return twos_complement(int(time.monotonic() * 60))
        else:
            raise NotImplementedError(f"built-in variable {name} not implemented")

    def eval_builtin_function(self, name, args):
        if name == "ABS" and len(args) == 1:
            return twos_complement(abs(self.eval(args[0])))
        elif name == "SQR" and len(args) == 1:
            return twos_complement(math.isqrt(self.eval(args[0])))
        elif name == "MOD" and len(args) == 2:
            return twos_complement(self.eval(args[0]) % self.eval(args[1]))
        elif name == "RND" and len(args) <= 1:
            # TODO: test this?
            # reference: page 273
            # "The function has two forms, one that accepts a number as the random seed value, and a no-argument form that returns the next random number in the sequence."
            if len(args) == 1:
                seed = self.eval(args[0])
                assert isinstance(seed, int)
                if seed == 0:
                    # "A seed value of zero is invalid and will be replaced with the system's default seed value."
                    random.seed()
                else:
                    # "For a given seed value the resulting sequence will always be the same."
                    random.seed(seed)
            # "[...] generate random numbers between 0 and 255."
            return random.randrange(256)
        elif name == "NOT" and len(args) == 1:
            return ~self.eval(args[0])
        elif name == "AND" and len(args) == 2:
            return self.eval(args[0]) & self.eval(args[1])
        elif name == "OR" and len(args) == 2:
            return self.eval(args[0]) | self.eval(args[1])
        elif name == "XOR" and len(args) == 2:
            return self.eval(args[0]) ^ self.eval(args[1])
        elif name == "SUB$" and len(args) == 3:
            s = self.eval(args[0])
            start = self.eval(args[1])
            length = self.eval(args[2])
            assert (
                isinstance(s, str)
                and 0 <= start < len(s)
                and 0 <= length
                and start + length < len(s)
            )
            return s[start : start + length]
        elif name == "CHR$":
            # TODO: use CODSCII charset (extended ascii)
            return "".join(map(lambda x: chr(self.eval(x)), args))
        elif name == "STR$" and len(args) == 1:
            return str(self.eval(args[0]))
        elif name == "VAL" and len(args) == 1:
            # "returns the number it was able to parse from the beginning of the string"
            s = self.eval(args[0])
            assert isinstance(s, str)
            digits = []
            for i, c in enumerate(s):
                # "Leading minus signs are supported"
                if c.isdigit() or (i == 0 and c == "-"):
                    digits.append(c)
                else:
                    break
            return twos_complement(int("".join(digits)))
        elif name == "LEN" and len(args) == 1:
            return len(self.eval(args[0]))
        elif name == "ASC" and len(args) == 1:
            s = self.eval(args[0])
            assert isinstance(s, str)
            if len(s) > 0:
                return ord(s[0])
            else:
                return 0
        else:
            raise NotImplementedError(
                f"built-in function {name}/{len(args)} not implemented"
            )

    def run_command(self, command):
        if command.command_type in ("REM", "DATA"):
            pass  # ignore comments and (already precomputed) DATA values
        elif command.command_type == "ASSIGNMENT":
            index, target = self.compute_target(command.lvalue)
            value = self.eval(command.rvalue)
            self.add_value(target, value, index)
        elif command.command_type == "PRINT":
            value = ""
            for expr in command.expressions:
                # TODO: implement AT and TAB functions in eval via IO
                v = self.eval(expr)
                if v is not None:
                    self.io.print(str(v))

            if not command.no_new_line:
                self.io.println()
        elif command.command_type == "INPUT":
            for expr in command.expressions:
                index, target = self.compute_target(expr)
                value = self.io.input()
                self.add_value(target, value, index, convert_int=True)
        elif command.command_type == "IF":
            value = self.eval(command.condition)
            if value:
                self.run_command(command.command)
        elif command.command_type == "GOTO":
            number = self.eval(command.expression)
            assert isinstance(number, int)
            # TODO: precompute hashmap with jump target to do this in O(1)
            for index, target in enumerate(self.code):
                if target.line_number == number:
                    self.next_index = index
                    break
        elif command.command_type == "FOR":
            self.run_command(command.assignment)
            limit = self.eval(command.limit)
            variable = command.assignment.lvalue
            assert variable.ast_type == ASTTypes.IntegerVariable
            self.loop_stack.append((variable.name, limit, self.next_index))
            assert self.int_arrays[variable.name][0] < limit
        elif command.command_type == "NEXT":
            name, limit, next_index = self.loop_stack[-1]
            current_value = self.int_arrays[name][0]
            if current_value == limit:
                pass
            else:
                self.int_arrays[name][0] = current_value + 1
                self.next_index = next_index
        elif command.command_type == "GOSUB":
            number = self.eval(command.expression)
            assert isinstance(number, int)
            self.call_stack.append(self.next_index)
            # TODO: precompute hashmap with jump target to do this in O(1)
            for index, target in enumerate(self.code):
                if target.line_number == number:
                    self.next_index = index
                    break
        elif command.command_type == "RETURN":
            self.next_index = self.call_stack.pop()
        elif command.command_type == "END":
            self.next_index = len(self.code)  # FIXME: remove hack
        elif command.command_type == "READ":
            for expr in command.expressions:
                index, target = self.compute_target(expr)
                # only integer variables supported
                assert target.ast_type == ASTTypes.IntegerVariable
                value = self.read_next_data_value()
                self.add_value(target, value, index)
        elif command.command_type == "RESTORE":
            self.reset_data_pos()
        else:
            raise NotImplementedError(f"unknown command {command.command_type}")

    def run_code(self, code):
        # TODO: remove unexpected side-effect from run_code
        self.setup_data_segment(code)
        self.code = code
        self.next_index = 0
        while self.next_index < len(code):
            command = code[self.next_index]
            self.next_index += 1
            self.run_command(command)

    def reset(self):
        self.int_arrays = {}  # maps variable names to values
        self.string_arrays = {}  # maps variable names to values
        self.call_stack = []
        self.loop_stack = []
        self.reset_data_pos()
        self.data_segment = []
        self.code = []
        self.next_index = 0

    def reset_data_pos(self):
        self.data_pos = (0, 0)

    def setup_data_segment(self, code):
        """
        Precomputes the DATA values by evaluating all data statements.
        """
        # values will be added by DATA statement
        for command in code:
            if command.command_type == "DATA":
                values = []
                for expr in command.expressions:
                    value = self.eval(expr)
                    values.append(value)
                self.data_segment.append(values)

    def read_next_data_value(self):
        line, index = self.data_pos
        value = self.data_segment[line][index]
        if len(self.data_segment[line]) == index + 1:
            self.data_pos = (line + 1, 0)
        else:  # move to next "line"
            self.data_pos = (line, index + 1)
        return value


class StdIO(IO):
    def print(self, value: str):
        print(value, end="")

    def println(self):
        print()

    def input(self) -> str:
        return input("? ")


class TestIO(IO):
    # https://stackoverflow.com/questions/62460557/cannot-collect-test-class-testmain-because-it-has-a-init-constructor-from
    __test__ = False

    def __init__(
        self, inputs: Optional[Iterable[str]] = None, print_inputs: bool = False
    ):
        self.inputs = list(inputs) if inputs else None
        self.print_inputs: bool = print_inputs
        self.output_log: list[str] = []
        # flag to indicate that the last input ended on a newline
        self.new_line: bool = True

    def print(self, value: str):
        if self.new_line:
            self.output_log.append("")
            self.new_line = False
        self.output_log[-1] += value

    def println(self):
        self.print("")
        self.new_line = True

    def input(self) -> str:
        result = str(self.inputs.pop(0))
        if self.print_inputs:
            self.print("? ")
            self.print(result)
            self.println()
        elif not self.new_line:
            # print new line after custom prompt if required
            self.println()
        return result
