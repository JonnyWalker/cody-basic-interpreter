# for repl: python cody_basic.py
# for graphical: python cody_basic.py [-g|--graphical]
# for run a file: python cody_basic.py examples/simple_array.bas

import argparse
import os
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
    interp.load(parsed)
    interp.run()


def main():
    parser = argparse.ArgumentParser(
        prog=f"{os.path.basename(__file__)}", description="Cody BASIC"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="run the given file, if not given the REPL will be started instead",
    )
    parser.add_argument(
        "-g",
        "--graphical",
        action="store_true",
        help="start graphical emulator",
    )
    args = parser.parse_args()

    if args.graphical:
        import cody_pygame

        cody_pygame.start(args.file)
    elif args.file:
        run_file(args.file)
    else:
        repl()


if __name__ == "__main__":
    main()
