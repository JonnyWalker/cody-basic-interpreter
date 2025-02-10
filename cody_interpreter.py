from cody_parser import ASTTypes
from abc import ABC, abstractmethod
from typing import Optional, Iterable


class IO(ABC):
    @abstractmethod
    def print(self, value): ...

    @abstractmethod
    def println(self): ...

    @abstractmethod
    def input(self) -> str: ...


class Interpreter:
    def __init__(self, io: Optional[IO] = None):
        self.int_arrays = {}  # maps variable names to values
        self.string_arrays = {}  # maps variable names to values
        self.call_stack = []
        self.loop_stack = []
        self.io = io if io is not None else StdIO()

    def compute_target(self, node):
        if node.ast_type == ASTTypes.ArrayExpression:
            index = node.index
            target = node.subnode
        else:
            index = 0
            target = node
        return index, target

    def add_value(self, target, value, index):
        if target.ast_type == ASTTypes.IntegerVariable:
            array = self.int_arrays.get(target.name, dict())
            array[index] = int(value)
            self.int_arrays[target.name] = array
        elif target.ast_type == ASTTypes.StringVariable:
            array = self.string_arrays.get(target.name, dict())
            array[index] = value
            self.string_arrays[target.name] = array

    def eval(self, node):
        if node.ast_type == ASTTypes.Equal:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left == right
        elif node.ast_type == ASTTypes.NotEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left != right
        elif node.ast_type == ASTTypes.Less:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left < right
        elif node.ast_type == ASTTypes.LessEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left <= right
        elif node.ast_type == ASTTypes.Greater:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left > right
        elif node.ast_type == ASTTypes.GreaterEqual:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left >= right
        elif node.ast_type == ASTTypes.BinaryAdd:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left + right
        elif node.ast_type == ASTTypes.BinarySub:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left - right
        elif node.ast_type == ASTTypes.BinaryMul:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left * right
        elif node.ast_type == ASTTypes.BinaryDiv:
            left = self.eval(node.left)
            right = self.eval(node.right)
            return left // right  # integer div
        elif node.ast_type == ASTTypes.UnaryMinus:
            expr = self.eval(node.expr)
            return -expr
        elif node.ast_type == ASTTypes.StringLiteral:
            return node.literal
        elif node.ast_type == ASTTypes.IntegerLiteral:
            return node.value
        elif node.ast_type in (
            ASTTypes.IntegerVariable,
            ASTTypes.StringVariable,
            ASTTypes.ArrayExpression,
        ):
            index, target = self.compute_target(node)
            if target.ast_type == ASTTypes.IntegerVariable:
                return self.int_arrays[target.name][index]
            elif target.ast_type == ASTTypes.StringVariable:
                return self.string_arrays[target.name][index]
            else:
                raise AssertionError
        else:
            raise Exception("eval error")

    def run_command(self, command):
        if command.command_type == "REM":
            pass  # ignore line
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
                self.add_value(target, value, index)
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
        else:
            raise NotImplementedError(f"unknown command {command.command_type}")

    def run_code(self, code):
        self.code = code
        self.next_index = 0
        while self.next_index < len(code):
            command = code[self.next_index]
            self.next_index += 1
            self.run_command(command)


class StdIO(IO):
    def print(self, value: str):
        print(value, end="")

    def println(self):
        print()

    def input(self) -> str:
        return input("? ")


class TestIO(IO):
    def __init__(self, inputs: Optional[Iterable[str]] = None):
        self.inputs = list(inputs) if inputs else None
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
        return str(self.inputs.pop(0))
