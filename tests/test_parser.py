from cody_parser import parse_command
from cody_parser import ASTTypes

def test_parse_simple_add():
    code = '10 PRINT 3+4' # book page 247
    command = parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.BinaryAdd
    assert command.expression.left.ast_type == ASTTypes.IntegerLiteral
    assert command.expression.right.ast_type == ASTTypes.IntegerLiteral
    assert command.expression.left.value == 3
    assert command.expression.right.value == 4

def test_parse_hello_world():
    code = '10 PRINT "Hello"' # book page 248
    command = parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.StringLiteral
    assert command.expression.literal == "Hello"

def test_parse_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";' # book page 250
    command = parse_command(code)
    assert command.line_number == 10
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.StringLiteral
    assert command.expression.literal == "WHAT IS YOUR NAME"

def test_parse_string_var():
    code = '20 INPUT N$' # book page 250
    command = parse_command(code)
    assert command.line_number == 20
    assert command.command_type == "INPUT"
    assert command.expression.ast_type == ASTTypes.StringVariable
    assert command.expression.name == "N"

def test_parse_integer_var():
    code = '40 INPUT A' # book page 250
    command = parse_command(code)
    assert command.line_number == 40
    assert command.command_type == "INPUT"
    assert command.expression.ast_type == ASTTypes.IntegerVariable
    assert command.expression.name == "A"

def test_parse_expression_list():
    code = '50 PRINT N$," IS ",A," YEARS OLD."' # book page 250
    command = parse_command(code)
    assert command.line_number == 50
    assert command.command_type == "PRINT"
    assert command.expression.ast_type == ASTTypes.ExpressionList
    assert command.expression.expr_list[0].ast_type == ASTTypes.StringVariable
    assert command.expression.expr_list[1].ast_type == ASTTypes.StringLiteral
    assert command.expression.expr_list[2].ast_type == ASTTypes.IntegerVariable
    assert command.expression.expr_list[3].ast_type == ASTTypes.StringLiteral