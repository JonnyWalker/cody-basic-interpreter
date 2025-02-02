from cody_parser import ASTTypes


class Interpreter:
    def __init__(self):
        self.cody_output_log = [] # used for test cases and maybe (later) for debugging
        self.int_arrays = {} # maps variable names to values
        self.string_arrays = {} # maps variable names to values
        self.call_stack = []
    
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
        return self.eval_list(node)
    
    def eval_list(self, node):
        if node.ast_type == ASTTypes.ExpressionList:
            result = ""
            for n in node.expr_list:
                result += self.eval_equality(n) # TODO: what if not a string?
            return result
        else:
            return self.eval_equality(node)

    def eval_equality(self, node):
        return self.eval_comparison(node)

    def eval_comparison(self, node):
        if node.ast_type == ASTTypes.Less:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left < right
        elif node.ast_type == ASTTypes.Equal:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left == right
        elif node.ast_type == ASTTypes.Greater:
            left = self.eval_term(node.left)
            right = self.eval_term(node.right)
            return left > right
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
            return left // right # integer div
        else:
            return self.eval_unary(node)

    def eval_unary(self, node):
        return self.eval_primary(node)

    def eval_primary(self, node):
        if node.ast_type == ASTTypes.StringLiteral:
            return node.literal
        elif node.ast_type == ASTTypes.IntegerLiteral:
            return node.value
        elif node.ast_type == ASTTypes.IntegerVariable:
            return self.int_arrays[node.name][0]
        elif node.ast_type == ASTTypes.StringVariable:
            return self.string_arrays[node.name][0]
        elif node.ast_type == ASTTypes.ArrayExpression: # TODO: dry
            index = node.index
            if node.subnode.ast_type == ASTTypes.IntegerVariable:
                return self.int_arrays[node.subnode.name][index]
            elif node.subnode.ast_type == ASTTypes.StringVariable:
                return self.string_arrays[node.subnode.name][index]            
        else:
            print("eval error")
        
    def run_command(self, command):
        if command.command_type == "REM":
            pass
        elif command.command_type == "ASSIGNMENT":
            index, target = self.compute_target(command.lvalue)
            value = self.eval(command.rvalue)
            self.add_value(target, value, index)    
        elif command.command_type == "POKE":
            pass
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
            value = self.eval(command.expression)
            self.cody_output_log.append(value)
            # https://stackoverflow.com/questions/493386/how-to-print-without-a-newline-or-space
            if command.no_new_line:
                print(value, end='')
            else:
                print(value)
        elif command.command_type == "IF":
            value = self.eval(command.condition)
            if value:
                self.run_command(command.command)
        elif command.command_type == "INPUT":
            print("? ", end='')
            index, target = self.compute_target(command.expression)
            value = input()
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
            pass
        elif command.command_type == "FOR":
            pass
        elif command.command_type == "RETURN":
            self.next_index = self.call_stack.pop()
        elif command.command_type == "END":
            self.next_index = len(self.code)  # FIXME: remove hack 
    
    def run_code(self, code):
        self.code = code
        self.next_index = 0
        while self.next_index < len(code):
            command = code[self.next_index]
            self.next_index += 1
            self.run_command(command)