from cody_parser import CodyBasicParser, ASTTypes, ASTNode, CommandTypes, Command
from abc import ABC, abstractmethod
from typing import Optional, Iterable, Literal
from cody_util import to_unsigned, twos_complement, check_string
import time
import random
import math


class IO(ABC):
    def __init__(self):
        self.uart: Optional[int] = None
        self.bit_rate: Optional[int] = None

    def print(self, value: str):
        assert isinstance(value, str)
        for c in value:
            n = ord(c)
            assert 0 <= n < 256
            if n == 10:
                self.println()
            elif n == 222:
                self.clear_screen()
            elif n == 223:
                self.reverse_field()
            elif n >= 240:
                self.set_foreground_color(n - 240)
            elif n >= 224:
                self.set_background_color(n - 224)
            else:
                self.print_char(c)

    @abstractmethod
    def print_char(self, c: str): ...

    @abstractmethod
    def println(self, value: str = ""): ...

    def clear_screen(self):
        raise NotImplementedError("clear_screen not implemented yet")

    def reverse_field(self):
        raise NotImplementedError("reverse_field not implemented yet")

    def set_background_color(self, c: int):
        raise NotImplementedError("set_background_color not implemented yet")

    def set_foreground_color(self, c: int):
        raise NotImplementedError("set_foreground_color not implemented yet")

    def print_at(self, col: int, row: int):
        raise NotImplementedError("AT not implemented yet")

    def print_tab(self, col: int):
        raise NotImplementedError("TAB not implemented yet")

    def open_uart(self, uart: int, bit_rate: int):
        assert self.uart is None and self.bit_rate is None
        assert uart in (1, 2) and bit_rate in range(1, 16)
        self.uart = uart
        self.bit_rate = bit_rate

    def close_uart(self):
        self.uart = None
        self.bit_rate = None

    def load_text(self, uart: int) -> list[str]:
        self.open_uart(uart, 15)  # bit rate 15 = 19200 baud
        try:
            lines = []
            while line := self.input("?"):  # no space
                lines.append(line)
        finally:
            self.close_uart()
        return lines

    def save_text(self, uart: int, lines: Iterable[str]):
        self.open_uart(uart, 15)  # bit rate 15 = 19200 baud
        try:
            for line in lines:
                self.print(line)
                self.println()
        finally:
            self.close_uart()

    @abstractmethod
    def input(self, prompt: str) -> str: ...

    def prompt_char(self) -> str:
        return "?"

    def peek(self, address: int) -> int:
        raise NotImplementedError("PEEK not implemented yet")

    def poke(self, address: int, value: int):
        raise NotImplementedError("POKE not implemented yet")

    def sys(self, address: int):
        raise NotImplementedError("SYS not implemented yet")

    def get_time(self) -> int | float | str:
        return time.monotonic() * 60


class Interpreter:
    def __init__(self, io: Optional[IO] = None):
        self.io = io if io is not None else StdIO()
        self.program = []  # sorted list of commands (by line number)
        self.running: bool = False  # True if running program, False if in repl mode
        self.call_stack: list[int] = []
        self.loop_stack: list[tuple[str, int, int, int]] = []
        self.int_arrays: dict[str, dict[str, int]] = {}
        self.strings: dict[str, str] = {}
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
        self.strings.clear()
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
            value = self.strings.setdefault(target.name, "")
            return check_string(value)
        else:
            raise ValueError(f"cannot read from node {target.ast_type.name}")

    def set_value(
        self, target: ASTNode, index: int, value: int | str, convert_int: bool = False
    ):
        if target.ast_type == ASTTypes.IntegerVariable:
            value = twos_complement(value, convert=convert_int)
            self.int_arrays.setdefault(target.name, {})[index] = value
        elif target.ast_type == ASTTypes.StringVariable:
            # string arrays not supported
            assert index == 0
            value = check_string(value)
            self.strings[target.name] = value
        else:
            raise ValueError(f"cannot write to node {target.ast_type.name}")

    def eval(self, node):
        if node.ast_type == ASTTypes.Equal:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and type(left) == type(right)
            return left == right
        elif node.ast_type == ASTTypes.NotEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and type(left) == type(right)
            return left != right
        elif node.ast_type == ASTTypes.Less:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and type(left) == type(right)
            return left < right
        elif node.ast_type == ASTTypes.LessEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and type(left) == type(right)
            return left <= right
        elif node.ast_type == ASTTypes.Greater:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and type(left) == type(right)
            return left > right
        elif node.ast_type == ASTTypes.GreaterEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and type(left) == type(right)
            return left >= right
        elif node.ast_type == ASTTypes.BinaryAdd:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, (int, str)) and isinstance(right, (int, str))
            if isinstance(left, int) and isinstance(right, int):
                return twos_complement(left + right)
            else:
                return check_string(f"{left}{right}")
        elif node.ast_type == ASTTypes.BinarySub:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left - right)
        elif node.ast_type == ASTTypes.BinaryMul:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left * right)
        elif node.ast_type == ASTTypes.BinaryDiv:
            left = self.eval(node.left)
            right = self.eval(node.right)
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left // right)  # integer div
        elif node.ast_type == ASTTypes.UnaryMinus:
            expr = self.eval(node.expr)
            assert isinstance(expr, int)
            return twos_complement(-expr)
        elif node.ast_type == ASTTypes.StringLiteral:
            return check_string(node.literal)
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
            return twos_complement(self.io.get_time(), convert=True)
        else:
            raise NotImplementedError(f"built-in variable {name} not implemented")

    def eval_builtin_function(self, name, args):
        if name == "ABS" and len(args) == 1:
            expr = self.eval(args[0])
            assert isinstance(expr, int)
            return twos_complement(abs(expr))
        elif name == "SQR" and len(args) == 1:
            expr = self.eval(args[0])
            assert isinstance(expr, int)
            return twos_complement(math.isqrt(expr))
        elif name == "MOD" and len(args) == 2:
            left = self.eval(args[0])
            right = self.eval(args[1])
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left % right)
        elif name == "RND" and len(args) <= 1:
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
            expr = self.eval(args[0])
            assert isinstance(expr, int)
            return twos_complement(~expr)
        elif name == "AND" and len(args) == 2:
            left = self.eval(args[0])
            right = self.eval(args[1])
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left & right)
        elif name == "OR" and len(args) == 2:
            left = self.eval(args[0])
            right = self.eval(args[1])
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left | right)
        elif name == "XOR" and len(args) == 2:
            left = self.eval(args[0])
            right = self.eval(args[1])
            assert isinstance(left, int) and isinstance(right, int)
            return twos_complement(left ^ right)
        elif name == "SUB$" and len(args) == 3:
            s = self.eval(args[0])
            start = self.eval(args[1])
            length = self.eval(args[2])
            assert (
                isinstance(s, str)
                and isinstance(start, int)
                and isinstance(length, int)
                and 0 <= start < len(s)
                and 0 <= length < len(s) - start
            )
            return s[start : start + length]
        elif name == "CHR$":

            def codscii_chr(x):
                value = self.eval(x)
                assert 0 <= value < 256
                # TODO: use CODSCII charset (extended ascii)
                return chr(value)

            return check_string("".join(map(codscii_chr, args)))
        elif name == "STR$" and len(args) == 1:
            expr = self.eval(args[0])
            assert isinstance(expr, int)
            return check_string(expr, convert=True)
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
            return twos_complement("".join(digits), convert=True)
        elif name == "LEN" and len(args) == 1:
            expr = self.eval(args[0])
            assert isinstance(expr, str)
            return len(expr)
        elif name == "ASC" and len(args) == 1:
            s = self.eval(args[0])
            assert isinstance(s, str)
            if len(s) > 0:

                def codscii_ord(c):
                    # TODO: use CODSCII charset (extended ascii)
                    value = ord(c)
                    assert 0 <= value < 256
                    return value

                return codscii_ord(s[0])
            else:
                return 0
        elif name == "PEEK" and len(args) == 1:
            address = to_unsigned(self.eval(args[0]))
            return to_unsigned(self.io.peek(address), bits=8)
        elif name == "AT" and len(args) == 2:
            col = self.eval(args[0])
            row = self.eval(args[1])
            assert isinstance(col, int) and isinstance(row, int)
            self.io.print_at(col, row)
            return None
        elif name == "TAB" and len(args) == 1:
            row = self.eval(args[0])
            assert isinstance(row, int)
            self.io.print_tab(row)
            return None
        else:
            raise NotImplementedError(
                f"built-in function {name}/{len(args)} not implemented"
            )

    def _run_command(self, command: Command) -> Optional[int]:
        if getattr(self.io, "cancel", None):
            # TODO: hack
            self.io.cancel = False
            raise KeyboardInterrupt

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
            uart = self.eval(command.uart)
            mode = self.eval(command.mode)
            assert mode in (0, 1)
            if mode == 0:  # text mode
                lines = self.io.load_text(uart)
                parser = CodyBasicParser()
                parsed = self.parser.parse_lines(lines)
                self.load(parsed)
            else:
                raise NotImplementedError("LOAD in binary mode not supported")
        elif command.command_type == CommandTypes.SAVE:
            assert self.repl
            uart = self.eval(command.uart)
            self.io.save_text(uart, map(lambda cmd: cmd.source, self.program))
        elif command.command_type == CommandTypes.RUN:
            assert self.repl
            self.reset()
            # precondition: self.program must be sorted, so 0 is the first line
            next_index = 0
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
                v = self.eval(expr)
                if v is not None:
                    self.io.print(check_string(v, convert=True))

            if not command.no_new_line:
                self.io.println()
        elif command.command_type == CommandTypes.INPUT:
            assert self.running
            for expr in command.expressions:
                target, index = self.compute_target(expr)
                value = self.io.input(f"{self.io.prompt_char()} ")
                self.set_value(target, index, value, convert_int=True)
        elif command.command_type == CommandTypes.OPEN:
            assert self.running
            uart = self.eval(command.uart)
            bit_rate = self.eval(command.bit_rate)
            self.io.open_uart(uart, bit_rate)
        elif command.command_type == CommandTypes.CLOSE:
            assert self.running
            self.io.close_uart()
        elif command.command_type == CommandTypes.POKE:
            address = to_unsigned(self.eval(command.address))
            value = to_unsigned(self.eval(command.expression), bits=8)
            self.io.poke(address, value)
        elif command.command_type == CommandTypes.SYS:
            address = to_unsigned(self.eval(command.address))
            self.io.sys(address)
        elif command.command_type == CommandTypes.IF:
            value = self.eval(command.condition)
            assert isinstance(value, bool)
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
            # find next DATA command
            for i in range(self.data_pos, len(self.program)):
                cmd = self.program[i]
                if cmd.command_type == CommandTypes.DATA and cmd.expressions:
                    self.data_pos = i + 1
                    self.data_segment = list(map(self.eval, cmd.expressions))
                    break
            else:
                raise ValueError("no more data values")

        return self.data_segment.pop(0)


class StdIO(IO):
    def __init__(self):
        super().__init__()

    def print_char(self, c: str):
        if self.uart is not None or self.bit_rate is not None:
            raise NotImplementedError("printing to uart not supported")
        print(c, end="")

    def println(self, value: str = ""):
        if self.uart is not None or self.bit_rate is not None:
            raise NotImplementedError("printing to uart not supported")
        self.print(value)
        print()

    def input(self, prompt: str) -> str:
        if self.uart is not None or self.bit_rate is not None:
            raise NotImplementedError("reading from uart not supported")
        # can only read ascii printable chars from the console
        return check_string(input(prompt), allowed_chars="ascii_printable")


class TestIO(IO):
    # https://stackoverflow.com/questions/62460557/cannot-collect-test-class-testmain-because-it-has-a-init-constructor-from
    __test__ = False

    def __init__(
        self,
        *,
        inputs: Optional[Iterable[str]] = None,
        uart_inputs: Optional[dict[int, list[str]]] = None,
        print_prompts: bool = False,
        print_inputs: bool = False,
    ):
        super().__init__()
        self.inputs: list[str] = list(inputs) if inputs else []
        self.uart_inputs: dict[int, list[str]] = uart_inputs if uart_inputs else {}
        self.print_inputs = print_inputs
        self.print_prompts = print_inputs
        self.output_log: list[str] = []
        self.uart_log: dict[int, list[str]] = {}
        # flag to indicate whether the last printed line ended on a newline
        self.new_line: dict[Optional[int], bool] = {None: True, 1: True, 2: False}

    def _olog(self) -> list[str]:
        if self.uart is None:
            return self.output_log
        else:
            return self.output_log.setdefault(self.uart, [])

    def _ilog(self) -> list[str]:
        if self.uart is None:
            return self.inputs
        else:
            return self.uart_inputs.get(self.uart, [])

    def _check_new_line(self):
        if self.new_line[self.uart]:
            self._olog().append("")
            self.new_line[self.uart] = False

    def print_char(self, c: str):
        self._check_new_line()
        self._olog()[-1] += c

    def println(self, value: str = ""):
        self.print(value)
        self._check_new_line()
        self.new_line[self.uart] = True

    def input(self, prompt: str) -> str:
        result = str(self._ilog().pop(0))
        if self.print_prompts:
            self.print(prompt)
        if self.print_inputs:
            self.print(result)
        if self.print_prompts or self.print_inputs or not self.new_line:
            self.println()
        return result
