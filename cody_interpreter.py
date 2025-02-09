from cody_parser import ASTTypes


class Interpreter:
    def __init__(self):
        self.cody_output_log = []  # used for test cases and maybe (later) for debugging
        self.int_arrays = {}  # maps variable names to values
        self.string_arrays = {}  # maps variable names to values
        self.call_stack = []
        self.loop_stack = []

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
        return self.eval_comparison(node)

    def eval_comparison(self, node):
        if node.ast_type == ASTTypes.Equal:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left == right
        elif node.ast_type == ASTTypes.NotEqual:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left != right
        elif node.ast_type == ASTTypes.Less:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left < right
        elif node.ast_type == ASTTypes.LessEqual:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left <= right
        elif node.ast_type == ASTTypes.Greater:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left > right
        elif node.ast_type == ASTTypes.GreaterEqual:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left >= right
        else:
            return self.eval_term(node)

    def eval_term(self, node):
        if node.ast_type == ASTTypes.BinaryAdd:
            left = self.eval_factor(node.left)
            right = self.eval_factor(node.right)
            return left + right
        elif node.ast_type == ASTTypes.BinarySub:
            left = self.eval_factor(node.left)
            right = self.eval_factor(node.right)
            return left + right
        else:
            return self.eval_factor(node)

    def eval_factor(self, node):
        if node.ast_type == ASTTypes.BinaryMul:
            left = self.eval_unary(node.left)
            right = self.eval_unary(node.right)
            return left * right
        elif node.ast_type == ASTTypes.BinaryDiv:
            left = self.eval_unary(node.left)
            right = self.eval_unary(node.right)
            return left // right  # integer div
        else:
            return self.eval_unary(node)

    def eval_unary(self, node):
        return self.eval_primary(node)

    def eval_primary(self, node):
        if node.ast_type == ASTTypes.StringLiteral:
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
            pass
        elif command.command_type == "ASSIGNMENT":
            index, target = self.compute_target(command.lvalue)
            value = self.eval(command.rvalue)
            self.add_value(target, value, index)
        elif command.command_type == "POKE":
            pass  # TODO
        elif command.command_type == "GOSUB":
            number = self.eval(command.expression)
            assert isinstance(number, int)
            self.call_stack.append(self.next_index)
            # TODO: precompute hashmap with jump target to do this in O(1)
            for index, target in enumerate(self.code):
                if target.line_number == number:
                    self.next_index = index
                    break
        elif command.command_type == "PRINT":
            value = ""
            for expr in command.expressions:
                # TODO: implement AT and TAB functions
                value += str(self.eval(expr))

            if not self.cody_output_log or self.last_print_had_new_line:
                self.cody_output_log.append(value)
            else:
                self.cody_output_log[-1] += value

            if command.no_new_line:
                # https://stackoverflow.com/questions/493386/how-to-print-without-a-newline-or-space
                print(value, end="")
                self.last_print_had_new_line = False
            else:
                print(value)
                self.last_print_had_new_line = True
        elif command.command_type == "IF":
            value = self.eval(command.condition)
            if value:
                self.run_command(command.command)
        elif command.command_type == "INPUT":
            for expr in command.expressions:
                index, target = self.compute_target(expr)
                value = input("? ")
                self.add_value(target, value, index)
        elif command.command_type == "GOTO":
            number = self.eval(command.expression)
            assert isinstance(number, int)
            # TODO: precompute hashmap with jump target to do this in O(1)
            for index, target in enumerate(self.code):
                if target.line_number == number:
                    self.next_index = index
                    break
        elif command.command_type == "NEXT":
            name, limit, next_index = self.loop_stack[-1]
            current_value = self.int_arrays[name][0]
            if current_value == limit:
                pass
            else:
                self.int_arrays[name][0] = current_value + 1
                self.next_index = next_index
        elif command.command_type == "FOR":
            self.run_command(command.assignment)
            limit = self.eval(command.limit)
            variable = command.assignment.lvalue
            assert variable.ast_type == ASTTypes.IntegerVariable
            self.loop_stack.append((variable.name, limit, self.next_index))
            assert self.int_arrays[variable.name][0] < limit
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
