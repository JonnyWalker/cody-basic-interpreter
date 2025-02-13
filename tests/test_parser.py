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
    code = "10 PRINT ABS(-10)"  # book page 273
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
    code = "10 PRINT SQR(10)"  # book page 273
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
    code = "10 PRINT MOD(8,5)"  # book page 273
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
    code = "10 PRINT RND()"  # book page 274
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
    code = "10 PRINT RND(10)"  # book page 274
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
    code = "10 PRINT RND(TI)"  # book page 274
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


def test_parse_bitwise_example():
    code = [
        "10 INPUT A",
        "20 INPUT B",
        '30 PRINT "NOT ",NOT(A)',
        '40 PRINT "AND ",AND(A,B)',
        '50 PRINT "OR ",OR(A,B)',
        '60 PRINT "XOR ",XOR(A,B)',
    ]  # book page 275
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].command_type == "INPUT"
    assert parsed_code[1].command_type == "INPUT"
    assert parsed_code[2].command_type == "PRINT"
    assert parsed_code[2].expressions[1].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[2].expressions[1].name == "NOT"
    assert parsed_code[3].expressions[1].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[3].expressions[1].name == "AND"
    assert parsed_code[4].expressions[1].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[4].expressions[1].name == "OR"
    assert parsed_code[5].expressions[1].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[5].expressions[1].name == "XOR"


def test_parse_sub_call_example():
    code = [
        '10 A$="POMERANIAN"',
        "20 PRINT SUB$(A$,0,3)",
    ]  # book page 279
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "SUB$"


def test_parse_chr_call_example():
    code = [
        "10 PRINT CHR$(67,111,100,121)",
    ]  # book page 279
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].command_type == "PRINT"
    assert parsed_code[0].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[0].expressions[0].name == "CHR$"


def test_parse_str_call_example():
    code = """
10 INPUT N
20 S$=STR$(N)
30 PRINT S$
"""  # book page 280
    parser = CodyBasicParser()
    parsed_code = parser.parse_string(code)
    assert parsed_code[1].command_type == "ASSIGNMENT"
    assert parsed_code[1].rvalue.ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].rvalue.name == "STR$"


def test_parse_val_call_example():
    code = [
        "10 INPUT S$",
        "20 N=VAL(S$)",
        "30 PRINT N*2",
    ]  # book page 281
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "ASSIGNMENT"
    assert parsed_code[1].rvalue.ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].rvalue.name == "VAL"


def test_parse_len_call_example():
    code = [
        "10 INPUT S$",
        "20 PRINT LEN(S$)",
    ]  # book page 281
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "LEN"


def test_parse_asc_call_example():
    code = [
        "10 INPUT S$",
        "20 PRINT ASC(S$)",
    ]  # book page 282
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "ASC"


def test_parse_at_call_example():
    code = [
        "10 FOR I=0 TO 9",
        '20 PRINT AT(I,I),"HELLO, WORLD!"',
        "30 NEXT",
    ]  # book page 284
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "AT"


def test_parse_tab_call_example():
    code = [
        "10 FOR I=1 TO 10",
        '20 PRINT I,TAB(5),I*I,TAB(20),"MESSAGE"',
        "30 NEXT",
    ]  # book page 286
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[1].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[1].name == "TAB"
    assert parsed_code[1].expressions[3].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[3].name == "TAB"


def test_parse_chr_call_example():
    code = [
        "10 PRINT CHR$(222)",
    ]  # book page 287
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[0].command_type == "PRINT"
    assert parsed_code[0].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[0].expressions[0].name == "CHR$"


def test_parse_chr_call_example2():
    code = [
        "10 FOR I=0 TO 15",
        "20 PRINT CHR$(240+I),240+I",
        "30 NEXT",
        "40 PRINT CHR$(241)",
    ]  # book page 287
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "CHR$"
    assert parsed_code[3].command_type == "PRINT"
    assert parsed_code[3].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[3].expressions[0].name == "CHR$"


def test_parse_chr_call_example3():
    code = [
        "10 FOR I=0 TO 15",
        "20 PRINT CHR$(224+I),224+I",
        "30 NEXT",
        "40 PRINT CHR$(230)",
    ]  # book page 289
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "CHR$"
    assert parsed_code[3].command_type == "PRINT"
    assert parsed_code[3].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[3].expressions[0].name == "CHR$"


def test_parse_chr_call_example4():
    code = [
        "10 INPUT S$",
        "20 PRINT CHR$(223),S$,CHR$(223)",
    ]  # book page 290
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "PRINT"
    assert parsed_code[1].expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[0].name == "CHR$"
    assert parsed_code[1].expressions[2].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].expressions[2].name == "CHR$"


def test_parse_chr_call_example5():
    code = [
        "10 FOR I=0 TO 66",
        "20 IF MOD(I,6)=0 THEN PRINT",
        '30 PRINT 128+I," ",CHR$(128+I)," ";',
        "40 NEXT",
        "50 PRINT",
    ]  # book page 292
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[2].command_type == "PRINT"
    assert parsed_code[2].expressions[2].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[2].expressions[2].name == "CHR$"


def test_parse_ti_var():
    code = [
        "10 INPUT D",
        "20 D=D*60",
        "30 I=TI",
        "40 IF TI-I<D THEN GOTO 40",
    ]  # book page 301
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[2].command_type == "ASSIGNMENT"
    assert parsed_code[2].rvalue.ast_type == ASTTypes.BuiltInVariable
    assert parsed_code[2].rvalue.name == "TI"


def test_parse_peek_call_var():
    code = [
        '10 PRINT "PRESS Q TO QUIT..."',
        "20 IF AND(PEEK(16),1)=1 THEN GOTO 10",
        '30 PRINT "Q PRESSED"',
    ]  # book page 301
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    assert parsed_code[1].command_type == "IF"
    assert parsed_code[1].condition.ast_type == ASTTypes.Equal
    assert parsed_code[1].condition.left.ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].condition.left.name == "AND"
    assert parsed_code[1].condition.left.expressions[0].ast_type == ASTTypes.BuiltInCall
    assert parsed_code[1].condition.left.expressions[0].name == "PEEK"
