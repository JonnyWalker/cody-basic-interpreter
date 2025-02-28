import pygame
import argparse
import os
import sys
import threading
import traceback
import time
from typing import Optional
from cody_computer import CodyComputer, CodyIO
from cody_parser import CodyBasicParser
from cody_interpreter import Interpreter

COLOR_NAMES = [
    "black",
    "white",
    "red",
    "cyan",
    "purple",
    "green",
    "blue",
    "yellow",
    "orange",
    "brown",
    "lightsalmon",  # "lightred",
    "darkgray",
    "gray",
    "lightgreen",
    "lightblue",
    "lightgray",
]
COLORS = [pygame.colordict.THECOLORS[n] for n in COLOR_NAMES]

BORDER_TOP = 8
BORDER_LEFT = 4

KEYS = [
    pygame.K_q,
    pygame.K_e,
    pygame.K_t,
    pygame.K_u,
    pygame.K_o,
    pygame.K_a,
    pygame.K_d,
    pygame.K_g,
    pygame.K_j,
    pygame.K_l,
    (pygame.K_LSHIFT, pygame.K_RSHIFT),  # cody (makes numbers)
    pygame.K_x,
    pygame.K_v,
    pygame.K_n,
    (pygame.K_LCTRL, pygame.K_RCTRL),  # meta (makes punctuation)
    pygame.K_z,
    pygame.K_c,
    pygame.K_b,
    pygame.K_m,
    pygame.K_RETURN,  # arrow
    pygame.K_s,
    pygame.K_f,
    pygame.K_h,
    pygame.K_k,
    pygame.K_SPACE,
    pygame.K_w,
    pygame.K_r,
    pygame.K_y,
    pygame.K_i,
    pygame.K_p,
]

SCANCODE_TO_CHAR = [
    "",
    # no modifiers
    "Q",
    "E",
    "T",
    "U",
    "O",
    "A",
    "D",
    "G",
    "J",
    "L",
    "",  # cody
    "X",
    "V",
    "N",
    "",  # meta
    "Z",
    "C",
    "B",
    "M",
    "\n",  # arrow
    "S",
    "F",
    "H",
    "K",
    " ",
    "W",
    "R",
    "Y",
    "I",
    "P",
    "",
    "",
    # meta modifier
    "!",
    "#",
    "%",
    "&",
    "(",
    "@",
    "-",
    ":",
    "'",
    "]",
    "",  # meta+cody
    "<",
    ",",
    "?",
    "",  # meta+meta
    "\\",
    ">",
    ".",
    "/",
    "\b",  # meta+arrow=backspace
    "=",
    "+",
    ";",
    "[",
    " ",
    '"',
    "$",
    "^",
    "*",
    ")",
    "",
    "",
    # cody modifier
    "1",
    "3",
    "5",
    "7",
    "9",
    "A",
    "D",
    "G",
    "J",
    "L",
    "",  # cody+cody
    "X",
    "V",
    "N",
    "\x1B",  # cody+meta=escape
    "Z",
    "C",
    "B",
    "M",
    "\x18",  # cody+arrow=cancel
    "S",
    "F",
    "H",
    "K",
    " ",
    "2",
    "4",
    "6",
    "8",
    "0",
    "",
    "",
    # both meta and cody (does not exist on ROM)
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
]


class CodyRender:

    def __init__(self, cmp: CodyComputer, io: CodyIO):
        self.cmp = cmp
        self.io = io
        self.screen: Optional[pygame.Surface] = None

    def render(self):
        color_memory_start = 0xA000 + 0x400 * self.cmp.vid_color_memory
        color_memory = self.cmp.memget_multi(color_memory_start, 1000)
        character_memory_start = 0xA000 + 0x800 * self.cmp.vid_character_memory
        character_memory = self.cmp.memget_multi(character_memory_start, 2048)
        screen_memory_start = 0xA000 + 0x400 * self.cmp.vid_screen_memory
        screen_memory = self.cmp.memget_multi(screen_memory_start, 1000)
        color_bg = self.cmp.cursor_attr_bg
        color_fg = self.cmp.cursor_attr_fg

        border_color = COLORS[self.cmp.vid_border_color]
        self.screen.fill(border_color)

        for i, (char, local_color) in enumerate(zip(screen_memory, color_memory)):
            x = i % 40
            y = i // 40
            for yy in range(8):
                char_row_data = character_memory[8 * char + yy]
                for xx in range(4):
                    char_pixel_data = (char_row_data >> (2 * (3 - xx))) & 0b11
                    if char_pixel_data == 0:
                        color_index = local_color & 0xF
                    elif char_pixel_data == 1:
                        color_index = local_color >> 4
                    elif char_pixel_data == 2:
                        color_index = color_bg
                    elif char_pixel_data == 3:
                        color_index = color_fg

                    color = COLORS[color_index]
                    self.screen.set_at(
                        (BORDER_LEFT + x * 4 + xx, BORDER_TOP + y * 8 + yy), color
                    )

    def check_keyboard(self):
        pressed = pygame.key.get_pressed()

        def rd_kbd(keys):
            result = 0
            for i, k in enumerate(keys):
                if isinstance(k, int):
                    is_pressed = pressed[k]
                else:
                    is_pressed = False
                    for k_ in k:
                        if pressed[k_]:
                            is_pressed = True
                            break
                    else:
                        is_pressed = False
                result |= (0 if is_pressed else 1) << i
            return result

        # KEYSCAN
        self.cmp.keyboard_row_0 = rd_kbd(KEYS[0:5])
        self.cmp.keyboard_row_1 = rd_kbd(KEYS[5:10])
        self.cmp.keyboard_row_2 = rd_kbd(KEYS[10:15])
        self.cmp.keyboard_row_3 = rd_kbd(KEYS[15:20])
        self.cmp.keyboard_row_4 = rd_kbd(KEYS[20:25])
        self.cmp.keyboard_row_5 = rd_kbd(KEYS[25:30])
        self.cmp.joystick_1 = 0
        self.cmp.joystick_2 = 0

        # KEYDECODE
        self.cmp.key_mods = 0
        self.cmp.key_code = 0
        scancode = 0
        for row in (
            self.cmp.keyboard_row_0,
            self.cmp.keyboard_row_1,
            self.cmp.keyboard_row_2,
            self.cmp.keyboard_row_3,
            self.cmp.keyboard_row_4,
            self.cmp.keyboard_row_5,
        ):
            for _ in range(5):
                scancode += 1
                pressed = row & 0b1
                row >>= 1
                if not pressed:
                    if scancode == 0x0F:  # meta
                        self.cmp.key_mods |= 0x20
                    elif scancode == 0x0B:  # cody
                        self.cmp.key_mods |= 0x40
                    else:
                        self.cmp.key_code = scancode
        self.cmp.key_code |= self.cmp.key_mods

        # READKBD
        if self.cmp.key_code == self.cmp.key_debounce:
            if self.cmp.key_code != self.cmp.key_last:
                self.cmp.key_last = self.cmp.key_code
                if self.cmp.key_code == 0x60:
                    self.cmp.key_lock ^= 0x1
                elif (self.cmp.key_code & 0x1F) == 0:
                    # ignore modifier with no keys
                    # this makes sure escape (cody+meta, \x1B) will never show up as character
                    pass
                else:
                    key_typed = SCANCODE_TO_CHAR[self.cmp.key_code]

                    if key_typed == "\x18":
                        self.io.do_cancel()
                    elif key_typed:
                        # this condition does not exist in the original, but it increases safety
                        if self.cmp.key_lock:
                            key_typed = key_typed.lower()
                        self.io.on_key_typed(key_typed)
        else:
            self.cmp.key_debounce = self.cmp.key_code

    def start(self):
        # pygame setup
        pygame.init()

        # 40 cols, 4 horizontal pixels
        # 25 rows, 8 vertical pixels
        w, h = 160 + 2 * BORDER_LEFT, 200 + 2 * BORDER_TOP
        # SCALED makes the window not appear tiny on big screens
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((w, h), flags)
        pygame.display.set_caption("Cody BASIC")

        clock = pygame.time.Clock()
        running = True

        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break  # no need to process more events, we are quitting anyway

            if not running:
                break  # insta-close

            self.check_keyboard()
            self.io.blink()
            self.cmp.jiffies = (self.cmp.jiffies + 1) & 0xFFFF
            self.render()

            # flip() the display to put your work on screen
            pygame.display.flip()
            clock.tick(60)  # limits FPS to 60

        pygame.quit()


def start_basic(io: CodyIO):
    parser = CodyBasicParser()
    interpreter = Interpreter(io)

    io.println()
    io.println("  *** CODY COMPUTER BASIC V1.0emu ***  ")

    while True:
        source = io.input("\nREADY.\n")
        try:
            cmd = parser.parse_command(source)
            interpreter.run_command(cmd)
        except KeyboardInterrupt:
            io.println("\nINTERRUPT")
        except Exception:
            traceback.print_exc()
            io.println("\nERROR\n")


def start(file=None):
    cmp = CodyComputer()
    io = CodyIO(cmp)

    def load_into_queue(f, uart, encoding="utf-8"):
        source = f.read()
        if not isinstance(source, str):
            source = source.decode(encoding)
        for line in source.splitlines():
            line = line.strip()
            if line:
                io.input_queues[uart].put_nowait(line)
        io.input_queues[uart].put_nowait("")

    if file:
        # load given file code
        with open(file) as f:
            load_into_queue(f, 1)
    else:
        # load lander and trek code
        import urllib.request

        with urllib.request.urlopen(
            "https://raw.githubusercontent.com/fjmilens3/cody-computer/refs/heads/master/CodyBASIC/codylander.bas"
        ) as f:
            load_into_queue(f, 1)

        with urllib.request.urlopen(
            "https://raw.githubusercontent.com/fjmilens3/cody-computer/refs/heads/master/CodyBASIC/codytrek.bas"
        ) as f:
            load_into_queue(f, 2)

    t = threading.Thread(target=start_basic, args=[io])
    t.daemon = True
    t.start()

    render = CodyRender(cmp, io)
    render.start()


def main():
    parser = argparse.ArgumentParser(
        prog=f"{os.path.basename(__file__)}", description="Cody BASIC (Graphical)"
    )
    parser.add_argument("file", nargs="?", default=None)
    args = parser.parse_args()

    start(args.file)


if __name__ == "__main__":
    main()
