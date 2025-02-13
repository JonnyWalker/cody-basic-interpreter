# python cody_basic.py examples/simple_array.bas
import sys
from cody_parser import CodyBasicParser
from cody_interpreter import Interpreter


def main():
    parser = CodyBasicParser()
    parsed_code = parser.parse_file(sys.argv[1])
    interp = Interpreter()
    interp.run_code(parsed_code)


if __name__ == "__main__":
    main()
