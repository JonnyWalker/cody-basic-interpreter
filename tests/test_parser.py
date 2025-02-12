# python -m pytest -s
import pytest
from cody_parser import CodyBasicParser
from cody_parser import ASTTypes


def test_parse_simple_add():
    code = "10 PRINT 3+4"  # book page 247
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BinaryAdd
    assert ast.left.ast_type == ASTTypes.IntegerLiteral
    assert ast.right.ast_type == ASTTypes.IntegerLiteral
    assert ast.left.value == 3
    assert ast.right.value == 4


def test_parse_hello_world():
    code = '10 PRINT "HELLO"'  # book page 248
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.StringLiteral
    assert ast.literal == "HELLO"


def test_parse_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";'  # book page 250
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.no_new_line
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.StringLiteral
    assert ast.literal == "WHAT IS YOUR NAME"


def test_parse_string_var():
    code = "20 INPUT N$"  # book page 250
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 20
    assert command.command_type == "INPUT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.StringVariable
    assert ast.name == "N"


def test_parse_integer_var():
    code = "40 INPUT A"  # book page 250
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 40
    assert command.command_type == "INPUT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.IntegerVariable
    assert ast.name == "A"


def test_parse_expression_list():
    code = '50 PRINT N$," IS ",A," YEARS OLD."'  # book page 250
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 50
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 4
    assert command.expressions[0].ast_type == ASTTypes.StringVariable
    assert command.expressions[1].ast_type == ASTTypes.StringLiteral
    assert command.expressions[2].ast_type == ASTTypes.IntegerVariable
    assert command.expressions[3].ast_type == ASTTypes.StringLiteral


def test_parse_array_expression():
    code = "10 A(0)=10"  # book page 253
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "ASSIGNMENT"
    assert command.lvalue.ast_type == ASTTypes.ArrayExpression
    assert command.lvalue.index == 0
    assert command.lvalue.subnode.ast_type == ASTTypes.IntegerVariable
    assert command.rvalue.ast_type == ASTTypes.IntegerLiteral


def test_parse_variable_example():
    code = [
        "10 A(0)=10",
        "20 A(1)=20",
        "30 PRINT A+A(1)*3",
    ]  # book page 253
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].line_number == 10
    assert parsed_code[0].lvalue.ast_type == ASTTypes.ArrayExpression
    assert parsed_code[1].line_number == 20
    assert parsed_code[1].lvalue.ast_type == ASTTypes.ArrayExpression
    assert parsed_code[2].line_number == 30
    assert parsed_code[2].command_type == "PRINT"
    assert len(parsed_code[2].expressions) == 1
    ast = parsed_code[2].expressions[0]
    assert ast.ast_type == ASTTypes.BinaryAdd
    assert ast.left.ast_type == ASTTypes.IntegerVariable
    assert ast.right.ast_type == ASTTypes.BinaryMul
    assert ast.right.left.ast_type == ASTTypes.ArrayExpression
    assert ast.right.right.ast_type == ASTTypes.IntegerLiteral


def test_parse_if_example():
    code = [
        "10 INPUT N",
        '20 IF N<0 THEN PRINT "NEGATIVE"',
        '30 IF N=0 THEN PRINT "ZERO"',
        '40 IF N>0 THEN PRINT "POSITIVE"',
    ]  # book page 255
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].line_number == 10
    assert parsed_code[0].command_type == "INPUT"
    assert parsed_code[1].line_number == 20
    assert parsed_code[1].command_type == "IF"
    assert parsed_code[1].condition.ast_type == ASTTypes.Less
    assert parsed_code[1].command.command_type == "PRINT"
    assert parsed_code[2].line_number == 30
    assert parsed_code[2].command_type == "IF"
    assert parsed_code[2].condition.ast_type == ASTTypes.Equal
    assert parsed_code[2].command.command_type == "PRINT"
    assert parsed_code[3].line_number == 40
    assert parsed_code[3].command_type == "IF"
    assert parsed_code[3].condition.ast_type == ASTTypes.Greater
    assert parsed_code[3].command.command_type == "PRINT"


def test_parse_for_example():
    code = [
        "10 FOR I=1 TO 5",
        "20 PRINT I",
        "30 NEXT",
    ]  # book page 259
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].command_type == "FOR"
    assert parsed_code[0].assignment.command_type == "ASSIGNMENT"
    assert parsed_code[0].limit.ast_type == ASTTypes.IntegerLiteral
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[2].command_type == "NEXT"


def test_parse_math_expr():
    code = "10 PRINT 4+5*6-10"
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BinarySub
    assert ast.left.ast_type == ASTTypes.BinaryAdd
    assert ast.left.left.ast_type == ASTTypes.IntegerLiteral
    assert ast.left.left.value == 4
    assert ast.left.right.ast_type == ASTTypes.BinaryMul
    assert ast.left.right.left.ast_type == ASTTypes.IntegerLiteral
    assert ast.left.right.left.value == 5
    assert ast.left.right.right.ast_type == ASTTypes.IntegerLiteral
    assert ast.left.right.right.value == 6
    assert ast.right.ast_type == ASTTypes.IntegerLiteral
    assert ast.right.value == 10


def test_parse_builtin_abs():
    code = "10 PRINT ABS(-10)" # book page 273
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BuiltInCall
    assert ast.name == "ABS"
    assert ast.expressions[0].ast_type == ASTTypes.UnaryMinus
    assert ast.expressions[0].expr.ast_type == ASTTypes.IntegerLiteral   
    assert ast.expressions[0].expr.value == 10
 

def test_parse_builtin_sqrt():
    code = "10 PRINT SQR(10)" # book page 273
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BuiltInCall
    assert ast.name == "SQR"
    assert ast.expressions[0].ast_type == ASTTypes.IntegerLiteral  
    assert ast.expressions[0].value == 10


def test_parse_builtin_mod():
    code = "10 PRINT MOD(8,5)" # book page 273
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BuiltInCall
    assert ast.name == "MOD"
    assert ast.expressions[0].ast_type == ASTTypes.IntegerLiteral  
    assert ast.expressions[0].value == 8
    assert ast.expressions[1].ast_type == ASTTypes.IntegerLiteral  
    assert ast.expressions[1].value == 5


def test_parse_builtin_rnd_no_arg():
    code = "10 PRINT RND()" # book page 274
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BuiltInCall
    assert ast.name == "RND"
    assert ast.expressions == []


def test_parse_builtin_rnd():
    code = "10 PRINT RND(10)" # book page 274
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BuiltInCall
    assert ast.name == "RND"
    assert ast.expressions[0].ast_type == ASTTypes.IntegerLiteral  
    assert ast.expressions[0].value == 10


def test_parse_builtin_rnd_ti_arg():
    code = "10 PRINT RND(TI)" # book page 274
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert len(command.expressions) == 1
    ast = command.expressions[0]
    assert ast.ast_type == ASTTypes.BuiltInCall
    assert ast.name == "RND"
    assert ast.expressions[0].ast_type == ASTTypes.BuiltInVariable  
    assert ast.expressions[0].name == "TI"