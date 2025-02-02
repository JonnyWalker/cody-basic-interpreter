# python -m pytest -s
from cody_parser import CodyBasicParser
from cody_parser import ASTTypes

def test_parse_simple_add():
    code = '10 PRINT 3+4' # book page 247
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.BinaryAdd
    assert command.expression.left.ast_type == ASTTypes.IntegerLiteral
    assert command.expression.right.ast_type == ASTTypes.IntegerLiteral
    assert command.expression.left.value == 3
    assert command.expression.right.value == 4

def test_parse_hello_world():
    code = '10 PRINT "Hello"' # book page 248
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.StringLiteral
    assert command.expression.literal == "Hello"

def test_parse_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";' # book page 250
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.StringLiteral
    assert command.expression.literal == "WHAT IS YOUR NAME"

def test_parse_string_var():
    code = '20 INPUT N$' # book page 250
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 20
    assert command.command_type == "INPUT"
    assert command.expression.ast_type == ASTTypes.StringVariable
    assert command.expression.name == "N"

def test_parse_integer_var():
    code = '40 INPUT A' # book page 250
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 40
    assert command.command_type == "INPUT"
    assert command.expression.ast_type == ASTTypes.IntegerVariable
    assert command.expression.name == "A"

def test_parse_expression_list():
    code = '50 PRINT N$," IS ",A," YEARS OLD."' # book page 250
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 50
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.ExpressionList
    assert command.expression.expr_list[0].ast_type == ASTTypes.StringVariable
    assert command.expression.expr_list[1].ast_type == ASTTypes.StringLiteral
    assert command.expression.expr_list[2].ast_type == ASTTypes.IntegerVariable
    assert command.expression.expr_list[3].ast_type == ASTTypes.StringLiteral

def test_parse_array_expression():
    code = '10 A(0)=10' # book page 253
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "ASSIGNMENT"
    assert command.lvalue.ast_type == ASTTypes.ArrayExpression
    assert command.lvalue.index == 0
    assert command.lvalue.subnode.ast_type == ASTTypes.IntegerVariable
    assert command.rvalue.ast_type == ASTTypes.IntegerLiteral

def test_parse_variable_example():
    code = ['10 A(0)=10',
            '20 A(1)=20',
            '30 PRINT A+A(1)*3'] # book page 253
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].line_number == 10
    assert parsed_code[0].lvalue.ast_type == ASTTypes.ArrayExpression
    assert parsed_code[1].line_number == 20
    assert parsed_code[1].lvalue.ast_type == ASTTypes.ArrayExpression
    assert parsed_code[2].line_number == 30
    assert parsed_code[2].command_type == "PRINT"
    assert parsed_code[2].expression.ast_type == ASTTypes.BinaryAdd
    assert parsed_code[2].expression.left.ast_type == ASTTypes.IntegerVariable
    assert parsed_code[2].expression.right.ast_type == ASTTypes.BinaryMul
    assert parsed_code[2].expression.right.left.ast_type == ASTTypes.ArrayExpression
    assert parsed_code[2].expression.right.right.ast_type == ASTTypes.IntegerLiteral

def test_parse_if_example():
    code = ['10 INPUT N',
            '20 IF N<0 THEN PRINT "NEGATIVE"',
            '30 IF N=0 THEN PRINT "ZERO"',
            '40 IF N>0 THEN PRINT "POSITIVE"'] # book page 255
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