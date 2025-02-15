from cody_parser import ASTTypes, ASTNode, CommandTypes, Command
from abc import ABC, abstractmethod
from typing import Optional, Iterable, Literal
from cody_util import to_unsigned, twos_complement
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

    def peek(self, address: int) -> int:
        raise NotImplementedError("PEEK not implemented yet")

    def poke(self, address: int, value: int):
        raise NotImplementedError("POKE not implemented yet")

    def sys(self, address: int):
        raise NotImplementedError("SYS not implemented yet")


class Interpreter:
    def __init__(self, io: Optional[IO] = None):
        self.io = io if io is not None else StdIO()
        self.program = []  # sorted list of commands (by line number)
        self.running: bool = False  # True if running program, False if in repl mode
        self.call_stack: list[int] = []
        self.loop_stack: list[tuple[str, int, int, int]] = []
        self.int_arrays: dict[str, dict[str, int]] = {}
        self.string_arrays: dict[str, dict[str, str]] = {}
        self.data_pos: int = 0
        self.data_segment: list[int] = []

    @property
    def repl(self):
        return not self.running

    def reset(self, program=False):
        if program:
            self.program.clear()
        self.running = False
        self.call_stack.clear()
        self.loop_stack.clear()
        self.int_arrays.clear()
        self.string_arrays.clear()
        self.data_pos = 0
        self.data_segment.clear()

    def find_line_number(
        self,
        line_number: int,
        mode: Literal["exact", "next"] = "exact",
        default: Optional[int] = None,
    ) -> Optional[int]:
        # precondition: self.program must be sorted!
        # TODO: smarter algorithm
        for i, cmd in enumerate(self.program):
            assert 0 <= cmd.line_number <= 65535
            if cmd.line_number == line_number and mode == "exact":
                return i
            elif cmd.line_number > line_number:
                if mode == "exact":
                    raise IndexError(f"could not find line number {line_number}")
                else:
                    return i
        return default

    def compute_target(self, node: ASTNode) -> tuple[ASTNode, int]:
        if node.ast_type == ASTTypes.ArrayExpression:
            target = node.subnode
            index = self.eval(node.index)
        elif node.ast_type in (ASTTypes.IntegerVariable, ASTTypes.StringVariable):
            target = node
            index = 0
        else:
            raise ValueError(f"cannot read/write to node {node.ast_type.name.name}")
        return target, index

    def get_value(self, target: ASTNode, index: int) -> int | str:
        if target.ast_type == ASTTypes.IntegerVariable:
            value = self.int_arrays.setdefault(target.name, {}).setdefault(index, 0)
            return twos_complement(value)
        elif target.ast_type == ASTTypes.StringVariable:
            # string arrays not supported
            assert index == 0
            value = self.string_arrays.setdefault(target.name, {}).setdefault(index, "")
            assert len(value) <= 255
            return value
        else:
            raise ValueError(f"cannot read from node {target.ast_type.name}")

    def set_value(
        self, target: ASTNode, index: int, value: int | str, convert_int: bool = False
    ):
        if target.ast_type == ASTTypes.IntegerVariable:
            if convert_int:
                value = int(value)
            else:
                assert isinstance(value, int)
            value = twos_complement(value)
            self.int_arrays.setdefault(target.name, {})[index] = value
        elif target.ast_type == ASTTypes.StringVariable:
            # string arrays not supported
            assert isinstance(value, str) and len(value) <= 255 and index == 0
            self.string_arrays.setdefault(target.name, {})[index] = value
        else:
            raise ValueError(f"cannot write to node {target.ast_type.name}")

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
            target, index = self.compute_target(node)
            return self.get_value(target, index)
        elif node.ast_type == ASTTypes.BuiltInVariable:
            return self.eval_builtin_var(node.name)
        elif node.ast_type == ASTTypes.BuiltInCall:
            return self.eval_builtin_function(node.name, node.expressions)
        else:
            raise NotImplementedError(f"ast type {node.ast_type.name} not implemented")

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
        elif name == "PEEK" and len(args) == 1:
            address = to_unsigned(self.eval(args[0]))
            return to_unsigned(self.io.peek(address), bits=8)
        else:
            raise NotImplementedError(
                f"built-in function {name}/{len(args)} not implemented"
            )

    def _run_command(self, command: Command) -> Optional[int]:
        if self.repl and command.line_number is not None:
            # repl mode but the command has a line number:
            # edit saved program
            self.load_command(command)
            return  # done

        next_index = "recalc"
        if command.command_type in (
            CommandTypes.REM,
            CommandTypes.EMPTY,
            CommandTypes.DATA,
        ):
            pass  # ignore comments and (already precomputed) DATA values
        elif command.command_type == CommandTypes.LIST:
            assert self.repl
            start = self.eval(command.start) if command.start else None
            end = self.eval(command.end) if command.end else None
            for cmd in self.program:
                if (start is None or start <= cmd.line_number) and (
                    end is None or cmd.line_number <= end
                ):
                    self.io.print(cmd.source)
                    self.io.println()
        elif command.command_type == CommandTypes.LOAD:
            assert self.repl
            # TODO: load from command.uart in mode command.mode
            raise NotImplementedError("LOAD not implemented yet")
        elif command.command_type == CommandTypes.SAVE:
            assert self.repl
            # TODO: save to command.uart
            raise NotImplementedError("SAVE not implemented yet")
        elif command.command_type == CommandTypes.RUN:
            assert self.repl
            self.reset()
            next_index = self.find_line_number(-1, mode="next")
        elif command.command_type == CommandTypes.NEW:
            assert self.repl
            self.reset(program=True)
        elif command.command_type == CommandTypes.ASSIGNMENT:
            target, index = self.compute_target(command.lvalue)
            value = self.eval(command.rvalue)
            self.set_value(target, index, value)
        elif command.command_type == CommandTypes.PRINT:
            value = ""
            for expr in command.expressions:
                # TODO: implement AT and TAB functions in eval via IO
                v = self.eval(expr)
                if v is not None:
                    self.io.print(str(v))

            if not command.no_new_line:
                self.io.println()
        elif command.command_type == CommandTypes.INPUT:
            assert self.running
            for expr in command.expressions:
                target, index = self.compute_target(expr)
                value = self.io.input()
                self.set_value(target, index, value, convert_int=True)
        elif command.command_type == CommandTypes.OPEN:
            assert self.running
            # TODO: open command.uart with command.bit_rate
            raise NotImplementedError("OPEN not implemented yet")
        elif command.command_type == CommandTypes.CLOSE:
            assert self.running
            # TODO: close opened uart
            raise NotImplementedError("CLOSE not implemented yet")
        elif command.command_type == CommandTypes.POKE:
            address = to_unsigned(self.eval(command.address))
            value = to_unsigned(self.eval(command.expression), bits=8)
            self.io.poke(address, value)
        elif command.command_type == CommandTypes.SYS:
            address = to_unsigned(self.eval(command.address))
            self.io.sys(address)
        elif command.command_type == CommandTypes.IF:
            value = self.eval(command.condition)
            if (
                value
                and (potential_jump_target := self._run_command(command.command))
                is not None
            ):
                next_index = potential_jump_target
        elif command.command_type == CommandTypes.GOTO:
            assert self.running
            target = self.eval(command.expression)
            assert isinstance(target, int)
            next_index = self.find_line_number(target)
        elif command.command_type == CommandTypes.FOR:
            assert self.running

            loop_var, loop_var_index = self.compute_target(command.loop_variable)
            assert loop_var.ast_type == ASTTypes.IntegerVariable
            initial = self.eval(command.initial)
            self.set_value(loop_var, loop_var_index, initial)

            limit = self.eval(command.limit)
            assert initial < limit
            self.loop_stack.append(
                (loop_var, loop_var_index, limit, command.line_number)
            )
        elif command.command_type == CommandTypes.NEXT:
            assert self.running
            loop_var, loop_var_index, limit, for_line_number = self.loop_stack[-1]
            current_value = self.get_value(loop_var, loop_var_index)
            if current_value >= limit:
                self.loop_stack.pop()
            else:
                self.set_value(loop_var, loop_var_index, current_value + 1)
                next_index = self.find_line_number(for_line_number, mode="next")
        elif command.command_type == CommandTypes.GOSUB:
            assert self.running
            target = self.eval(command.expression)
            assert isinstance(target, int)
            self.call_stack.append(command.line_number)
            next_index = self.find_line_number(target)
        elif command.command_type == CommandTypes.RETURN:
            assert self.running
            next_index = self.find_line_number(self.call_stack.pop(), mode="after")
        elif command.command_type == CommandTypes.END:
            assert self.running
            next_index = None
        elif command.command_type == CommandTypes.READ:
            for expr in command.expressions:
                target, index = self.compute_target(expr)
                # only integer variables supported
                assert target.ast_type == ASTTypes.IntegerVariable
                value = self.read_next_data_value()
                self.set_value(target, index, value)
        elif command.command_type == CommandTypes.RESTORE:
            self.data_pos = 0
            self.data_segment.clear()
        else:
            raise NotImplementedError(
                f"command type {command.command_type.name} not implemented"
            )

        if next_index == "recalc":
            if command.line_number is not None:
                return self.find_line_number(command.line_number, mode="next")
            else:
                return None
        else:
            return next_index

    def load(self, code: Iterable[Command]):
        self.run_command(Command(CommandTypes.NEW))
        for cmd in code:
            self.load_command(cmd)

    def load_command(self, command: Command):
        assert command.line_number is not None
        if command.command_type == CommandTypes.EMPTY:
            # remove
            try:
                del self.program[self.find_line_number(command.line_number)]
            except Exception:
                pass
        else:
            # save
            idx = self.find_line_number(
                command.line_number, mode="exact_or_next", default=len(self.program)
            )
            if (
                idx < len(self.program)
                and self.program[idx].line_number == command.line_number
            ):
                # override
                self.program[idx] = command
            else:
                # new line
                self.program.insert(idx, command)

    def run(self):
        self.run_command(Command(CommandTypes.RUN))

    def run_command(self, command: Command):
        assert self.repl
        next_index = self._run_command(command)
        self._run_loop(next_index)

    def _run_loop(self, next_index: Optional[int]):
        assert self.repl
        self.running = True
        try:
            while next_index is not None:
                cmd = self.program[next_index]
                next_index = self._run_command(cmd)
        finally:
            self.running = False

    def read_next_data_value(self):
        if not self.data_segment:
            if self.data_pos >= len(self.program):
                raise ValueError("no more data values")

            # find next DATA command
            for i in range(self.data_pos, len(self.program)):
                cmd = self.program[i]
                if cmd.command_type == CommandTypes.DATA:
                    self.data_pos = i + 1
                    self.data_segment = list(map(self.eval, cmd.expressions))
                    break

        return self.data_segment.pop(0)


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
