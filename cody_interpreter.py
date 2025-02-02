from cody_parser import ASTTypes


state = {} # maps variable names to values

class Interpreter:
    def __init__(self):
        self.cody_output_log = [] # used for test cases and maybe (later) for debugging

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
        return self.eval_unary(node)

    def eval_unary(self, node):
        return self.eval_primary(node)

    def eval_primary(self, node):
        if node.ast_type == ASTTypes.StringLiteral:
            return node.literal
        elif node.ast_type == ASTTypes.IntegerLiteral:
            return node.value
        else:
            print("eval error")
        
    def run_command(self, command):
        if command.command_type == "REM":
            pass
        elif command.command_type == "ASSIGNMENT":
            pass
        elif command.command_type == "POKE":
            pass
        elif command.command_type == "GOSUB":
            pass
        elif command.command_type == "PRINT":
            value = self.eval(command.expression)
            self.cody_output_log.append(value)
            # https://stackoverflow.com/questions/493386/how-to-print-without-a-newline-or-space
            if command.no_new_line:
                print(value, end='')
            else:
                print(value)
        elif command.command_type == "IF":
            pass
        elif command.command_type == "INPUT":
            pass
        elif command.command_type == "GOTO":
            pass
        elif command.command_type == "NEXT":
            pass
        elif command.command_type == "FOR":
            pass
        elif command.command_type == "RETURN":
            pass