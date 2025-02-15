# python cody_basic.py examples/simple_array.bas
import sys
import code
import math
import traceback
from cody_parser import CodyBasicParser, CommandTypes
from cody_interpreter import Interpreter

COMMANDS = [
    "NEW",
    "LOAD",
    "SAVE",
    "RUN",
    "LIST",
    "EXIT",
]


class CodyBasicREPL(code.InteractiveConsole):
    def __init__(self, parser, interpreter, *, local_exit=False, **kwargs):
        super().__init__(local_exit, **kwargs)
        self.parser = parser
        self.interpreter = interpreter

    def runsource(self, source, filename="<input>", symbol="single"):
        source = source.strip() if isinstance(source, str) else ""
        if not source:
            return
        elif source in ("EXIT", "QUIT"):
            raise SystemExit

        try:
            cmd = self.parser.parse_command(source)
            self.interpreter.run_command(cmd)
        except Exception:
            traceback.print_exc()


def repl():
    # for history support in REPL
    try:
        import readline
    except ImportError:
        pass

    parser = CodyBasicParser()
    interp = Interpreter()
    CodyBasicREPL(parser, interp).interact(banner="Cody BASIC")


def run_file():
    parser = CodyBasicParser()
    parsed_code = parser.parse_file(sys.argv[1])
    interp = Interpreter()
    interp.run_code(parsed_code)


def main():
    if len(sys.argv) < 2:
        repl()
    else:
        run_file()


if __name__ == "__main__":
    main()
