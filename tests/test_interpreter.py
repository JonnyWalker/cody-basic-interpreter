# python -m pytest -s
from cody_parser import CodyBasicParser
from cody_interpreter import Interpreter, TestIO
from typing import Optional, Iterable


def run_code(
    code: str, inputs: Optional[Iterable[str]] = None, print_inputs: bool = False
) -> Interpreter:
    parser = CodyBasicParser()
    parsed = parser.parse_string(code)
    interp = Interpreter(TestIO(inputs, print_inputs))
    interp.run_code(parsed)
    return interp


def test_simple_add():
    code = "10 PRINT 3+4"  # book page 247
    interp = run_code(code)
    assert interp.io.output_log == ["7"]


def test_hello_world():
    code = '10 PRINT "HELLO"'
    interp = run_code(code)
    assert interp.io.output_log == ["HELLO"]


def test_no_new_line_print():
    code = '10 PRINT "WHAT IS YOUR NAME";'  # book page 250
    interp = run_code(code)
    assert interp.io.output_log == ["WHAT IS YOUR NAME"]


def test_expression_list():
    code = '50 PRINT "CODY"," IS ",14," YEARS OLD."'  # book page 250 (modified)
    interp = run_code(code)
    assert interp.io.output_log == ["CODY IS 14 YEARS OLD."]


def test_array_expression():
    code = "10 A(0)=10"  # book page 253
    interp = run_code(code)
    assert interp.int_arrays["A"][0] == 10


def test_io_example():
    code = """
10 PRINT "WHAT IS YOUR NAME";
20 INPUT N$
30 PRINT "HOW OLD ARE YOU";
40 INPUT A
50 PRINT N$," IS ",A," YEARS OLD."
"""  # book page 250-251
    interp = run_code(code, ["CODY", "14"], print_inputs=True)
    assert interp.io.output_log == [
        "WHAT IS YOUR NAME? CODY",
        "HOW OLD ARE YOU? 14",
        "CODY IS 14 YEARS OLD.",
    ]


def test_variable_example():
    code = """
10 A(0)=10
20 A(1)=20
30 PRINT A+A(1)*3
"""  # book page 253
    interp = run_code(code)
    assert interp.int_arrays["A"][0] == 10
    assert interp.int_arrays["A"][1] == 20
    assert interp.io.output_log == ["70"]


def test_variable_example2():
    code = """
10 M$ = "HELLO "
20 N$ = "WORLD!"
30 PRINT M$,N$
"""  # book page 254
    interp = run_code(code)
    assert interp.string_arrays["M"][0] == "HELLO "
    assert interp.string_arrays["N"][0] == "WORLD!"
    assert interp.io.output_log == ["HELLO WORLD!"]


def test_if_example1():
    code = """
10 INPUT N
20 IF N<0 THEN PRINT "NEGATIVE"
30 IF N=0 THEN PRINT "ZERO"
40 IF N>0 THEN PRINT "POSITIVE"
"""  # book page 255
    interp = run_code(code, ["3"])
    assert interp.io.output_log == ["POSITIVE"]


def test_if_example2():
    code = """
10 INPUT S$
20 IF S$<"B" THEN PRINT "LESS"
30 IF S$="B" THEN PRINT "EQUAL"
40 IF S$>"B" THEN PRINT "GREATER"
"""  # book page 256
    interp = run_code(code, ["BA"])
    assert interp.io.output_log == ["GREATER"]


def test_goto_example():
    code = """
10 PRINT "A"
20 GOTO 40
30 PRINT "B"
40 PRINT "Z"
"""  # book page 257
    interp = run_code(code)
    assert interp.io.output_log == ["A", "Z"]


def test_gosub_example():
    code = """
10 PRINT "A"
20 GOSUB 50
30 PRINT "C"
40 END
50 PRINT "B"
60 RETURN
"""  # book page 258
    interp = run_code(code)
    assert interp.io.output_log == ["A", "B", "C"]


def test_for_example():
    code = """
10 FOR I=1 TO 5
20 PRINT I
30 NEXT
"""  # book page 259
    interp = run_code(code)
    assert interp.io.output_log == ["1", "2", "3", "4", "5"]


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
    interp = run_code(code)
    assert interp.io.output_log == [
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
    interp = run_code(code)
    assert interp.io.output_log == ["1", "23", "45678", "", "AB"]


def test_math_expr():
    code = """
10 PRINT 4+5*6-10
"""  # book page 270
    interp = run_code(code)
    assert interp.io.output_log == ["24"]


def test_math_div():
    code = """
10 PRINT 16/5
"""  # book page 270
    interp = run_code(code)
    assert interp.io.output_log == ["3"]


def test_math_expr_parens():
    code = """
10 PRINT 3*((8+2)/2)
"""  # book page 271
    interp = run_code(code)
    assert interp.io.output_log == ["15"]


def test_math_expr_unary_minus_1():
    code = """
10 PRINT -(1+2)
"""  # book page 271
    interp = run_code(code)
    assert interp.io.output_log == ["-3"]


def test_math_expr_unary_minus_2():
    code = """
10 A=20
20 B=2
30 PRINT -A*B
"""  # book page 272
    interp = run_code(code)
    assert interp.io.output_log == ["-40"]


def test_builtin_function_abs():
    code = """
10 PRINT ABS(-10)
"""  # book page 273
    interp = run_code(code)
    assert interp.io.output_log == ["10"]


def test_builtin_function_sqr():
    code = """
10 PRINT SQR(10)
"""  # book page 273
    interp = run_code(code)
    assert interp.io.output_log == ["100"]


def test_builtin_function_mod():
    code = """
10 PRINT MOD(8,5)
"""  # book page 273
    interp = run_code(code)
    assert interp.io.output_log == ["3"]


def test_string_concat():
    code = """
10 A$="HELLO"
20 B$="WORLD"
30 C$=A$+", "+B$+"!"
40 PRINT C$
"""  # book page 277
    interp = run_code(code)
    assert interp.io.output_log == ["HELLO, WORLD!"]


def test_string_comparisons():
    code = """
10 INPUT A$
20 INPUT B$
30 IF B$=A$+"!" THEN PRINT "MATCH"
"""  # book page 278
    interp = run_code(code, ["HELLO", "HELLO!"])
    assert interp.io.output_log == ["MATCH"]


def test_data():
    code = """
10 READ I
20 IF I<0 THEN GOTO 60
30 T=T+I
40 C=C+1
50 GOTO 10
60 PRINT "TOTAL ",T
70 PRINT "COUNT ",C
80 PRINT "AVERAGE ",T/C
90 DATA 3,10,12,7,6
100 DATA 3,15,8,2,-1
"""  # book page 299
    interp = run_code(code)
    assert interp.data_segment == [[3, 10, 12, 7, 6], [3, 15, 8, 2, -1]]
    assert interp.io.output_log == ["TOTAL 66", "COUNT 9", "AVERAGE 7"]
