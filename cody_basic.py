# python cody_basic.py examples/simple_array.bas
import sys
import code
import math
import traceback
from cody_parser import CodyBasicParser
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
        self.program = {}

    def runsource(self, source, filename="<input>", symbol="single"):
        source = source.strip()
        for cmd in COMMANDS:
            if source.startswith(cmd):
                break
        else:
            if len(source) > 0 and source[0].isdigit():
                # edit saved program
                try:
                    cmd = self.parser.parse_line(source, allow_empty=True)
                except Exception:
                    traceback.print_exc()
                    return
                if isinstance(cmd, int):
                    # remove
                    self.program.pop(cmd, None)
                else:
                    # save
                    self.program[cmd.line_number] = cmd, source
            else:
                # direct execution
                try:
                    cmd = self.parser.parse_statement(source)
                    self.interpreter.run_code([cmd])
                except Exception:
                    traceback.print_exc()
                    return
            return

        rest = self.parser.strip_whitespace(source[len(cmd) :])
        try:
            args = self.parser.parse(rest, list=True)
        except Exception:
            traceback.print_exc()
            return

        if cmd == "NEW":
            assert len(args) == 0
            self.program = {}
            self.interpreter.reset()
        elif cmd == "RUN":
            assert len(args) == 0
            sorted_code = sorted(
                [cmd for cmd, _ in self.program.values()],
                key=lambda cmd: cmd.line_number,
            )
            try:
                self.interpreter.run_code(sorted_code)
            except Exception:
                traceback.print_exc()
                return
        elif cmd == "LIST":
            assert len(args) <= 2
            if len(args) == 0:
                start = -math.inf
                end = math.inf
            elif len(args) == 1:
                start = self.interpreter.eval(args[0])
                end = math.inf
            elif len(args) == 2:
                start = self.interpreter.eval(args[0])
                end = self.interpreter.eval(args[1])
            for _, line in sorted(
                [
                    (cmd.line_number, line)
                    for cmd, line in self.program.values()
                    if start <= cmd.line_number <= end
                ]
            ):
                print(line)
        elif cmd == "EXIT":
            assert len(args) == 0
            raise SystemExit
        else:
            print(f"unknown command {cmd}")


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
