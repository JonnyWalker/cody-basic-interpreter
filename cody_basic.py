# for repl: python cody_basic.py
# for run a file: python cody_basic.py examples/simple_array.bas
import sys
import code
import traceback
from cody_parser import CodyBasicParser
from cody_interpreter import Interpreter


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


def run_file(filename):
    parser = CodyBasicParser()
    parsed = parser.parse_file(filename)
    interp = Interpreter()
    interp.load(parsed_code)
    interp.run()


def main():
    if len(sys.argv) < 2:
        repl()
    else:
        run_file(sys.argv[1])


if __name__ == "__main__":
    main()
