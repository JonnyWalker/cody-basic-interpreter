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
        self.program = {}

    def runsource(self, source, filename="<input>", symbol="single"):
        source = source.strip()
        if not source:
            return
        elif source in ("EXIT", "QUIT"):
            raise SystemExit

        cmd = self.parser.parse_command(source)

        if cmd.line_number is not None:
            # edit saved program
            if cmd.command_type == CommandTypes.EMPTY:
                # remove
                self.program.pop(cmd, None)
            else:
                # save
                self.program[cmd.line_number] = cmd, source
        # TODO: move this into interpreter
        elif cmd.command_type == CommandTypes.NEW:
            self.program = {}
            self.interpreter.reset()
        elif cmd.command_type == CommandTypes.RUN:
            sorted_code = sorted(
                [cmd for cmd, _ in self.program.values()],
                key=lambda cmd: cmd.line_number,
            )
            try:
                self.interpreter.run_code(sorted_code)
            except Exception:
                traceback.print_exc()
                return
        elif cmd.command_type == CommandTypes.LIST:
            start = self.interpreter.eval(cmd.start) if cmd.start else -math.inf
            end = self.interpreter.eval(cmd.end) if cmd.end else math.inf
            for _, line in sorted(
                [
                    (cmd.line_number, line)
                    for cmd, line in self.program.values()
                    if start <= cmd.line_number <= end
                ]
            ):
                print(line)
        else:
            # try direct execution
            try:
                self.interpreter.run_code([cmd])
            except Exception:
                traceback.print_exc()
                return


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
