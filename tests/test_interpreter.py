# python -m pytest -s
from cody_parser import CodyBasicParser
from cody_interpreter import Interpreter


def test_simple_add():
    code = '10 PRINT 3+4' # book page 247
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert 7 in interp.cody_output_log

def test_hello_world():
    code = '10 PRINT "Hello"'
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert "Hello" in interp.cody_output_log

def test_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";' # book page 250
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert "WHAT IS YOUR NAME" in interp.cody_output_log 

def test_expression_list():
    code = '50 PRINT "CODY"," IS ","14"," YEARS OLD."' # book page 250 (modified)
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert "CODY IS 14 YEARS OLD." in interp.cody_output_log

def test_array_expression():
    code = '10 A(0)=10' # book page 253
    parser = CodyBasicParser()
    command = parser.parse_command(code)
    interp = Interpreter()
    interp.run_command(command)
    assert interp.int_arrays["A"][0] == 10

def test_variable_example():
    code = ['10 A(0)=10',
            '20 A(1)=20',
            '30 PRINT A+A(1)*3'] # book page 253
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.int_arrays["A"][0] == 10
    assert interp.int_arrays["A"][1] == 20
    assert 70 in interp.cody_output_log