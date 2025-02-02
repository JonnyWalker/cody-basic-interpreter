from cody_parser import parse_command
from cody_interpreter import Interpreter


def test_simple_add():
    code = '10 PRINT 3+4' # book page 247
    command = parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert 7 in interp.cody_output_log

def test_hello_world():
    code = '10 PRINT "Hello"'
    command = parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert "Hello" in interp.cody_output_log

def test_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";' # book page 250
    command = parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert "WHAT IS YOUR NAME" in interp.cody_output_log 

def test_expression_list():
    code = '50 PRINT "CODY"," IS ","14"," YEARS OLD."' # book page 250 (modified)
    command = parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert "CODY IS 14 YEARS OLD." in interp.cody_output_log 