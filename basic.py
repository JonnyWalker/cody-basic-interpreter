# python basic.py tests/codylander.bas
import sys
from cody_parser import parse_file

def main():
    parse_file(sys.argv[1])

if __name__ == "__main__":
    main()

