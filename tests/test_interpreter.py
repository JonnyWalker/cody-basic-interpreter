# python -m pytest -s
from cody_parser import CodyBasicParser
from cody_interpreter import Interpreter


def test_simple_add():
    code = "10 PRINT 3+4"  # book page 247
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    interp = Interpreter()
    interp.run_command(command)
    assert interp.cody_output_log == ["7"]


def test_hello_world():
    code = '10 PRINT "HELLO"'
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    interp = Interpreter()
    interp.run_command(command)
    assert interp.cody_output_log == ["HELLO"]


def test_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";'  # book page 250
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    interp = Interpreter()
    interp.run_command(command)
    assert interp.cody_output_log == ["WHAT IS YOUR NAME"]


def test_expression_list():
    code = '50 PRINT "CODY"," IS ",14," YEARS OLD."'  # book page 250 (modified)
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    interp = Interpreter()
    interp.run_command(command)
    assert interp.cody_output_log == ["CODY IS 14 YEARS OLD."]


def test_array_expression():
    code = "10 A(0)=10"  # book page 253
    parser = CodyBasicParser()
    command = parser.parse_line(code)
    interp = Interpreter()
    interp.run_command(command)
    assert interp.int_arrays["A"][0] == 10


def test_variable_example():
    code = [
        "10 A(0)=10",
        "20 A(1)=20",
        "30 PRINT A+A(1)*3",
    ]  # book page 253
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.int_arrays["A"][0] == 10
    assert interp.int_arrays["A"][1] == 20
    assert interp.cody_output_log == ["70"]


def test_variable_example2():
    code = [
        '10 M$ = "HELLO "',
        '20 N$ = "WORLD!"',
        "30 PRINT M$,N$",
    ]  # book page 254
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.string_arrays["M"][0] == "HELLO "
    assert interp.string_arrays["N"][0] == "WORLD!"
    assert interp.cody_output_log == ["HELLO WORLD!"]


def test_goto_example():
    code = [
        '10 PRINT "A"',
        "20 GOTO 40",
        '30 PRINT "B"',
        '40 PRINT "Z"',
    ]  # book page 257
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.cody_output_log == ["A", "Z"]


def test_gosub_example():
    code = [
        '10 PRINT "A"',
        "20 GOSUB 50",
        '30 PRINT "C"',
        "40 END",
        '50 PRINT "B"',
        "60 RETURN",
    ]  # book page 257
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.cody_output_log == ["A", "B", "C"]


def test_for_example():
    code = [
        "10 FOR I=1 TO 5",
        "20 PRINT I",
        "30 NEXT",
    ]  # book page 259
    parser = CodyBasicParser()
    parsed_code = parser.parse_program(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.cody_output_log == ["1", "2", "3", "4", "5"]


def test_rel_ops():
    code = """
100 IF 1=1 THEN PRINT 10
110 IF 1<>1 THEN PRINT 11
120 IF 1<1 THEN PRINT 12
130 IF 1<=1 THEN PRINT 13
140 IF 1>1 THEN PRINT 14
150 IF 1>=1 THEN PRINT 15
200 IF 1=2 THEN PRINT 20
210 IF 1<>2 THEN PRINT 21
220 IF 1<2 THEN PRINT 22
230 IF 1<=2 THEN PRINT 23
240 IF 1>2 THEN PRINT 24
250 IF 1>=2 THEN PRINT 25
300 IF 2=1 THEN PRINT 30
310 IF 2<>1 THEN PRINT 31
320 IF 2<1 THEN PRINT 32
330 IF 2<=1 THEN PRINT 33
340 IF 2>1 THEN PRINT 34
350 IF 2>=1 THEN PRINT 35
"""
    parser = CodyBasicParser()
    parsed_code = parser.parse_string(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.cody_output_log == [
        "10",
        "13",
        "15",
        "21",
        "22",
        "23",
        "31",
        "34",
        "35",
    ]


def test_print():
    code = """
10 PRINT 1
20 PRINT 2, 3
30 PRINT 4, 5;
40 PRINT 6, 7;
50 PRINT 8
60 PRINT
70 PRINT "A";
80 PRINT "B";
90 PRINT
"""
    parser = CodyBasicParser()
    parsed_code = parser.parse_string(code)
    interp = Interpreter()
    interp.run_code(parsed_code)
    assert interp.cody_output_log == ["1", "23", "45678", "", "AB"]
