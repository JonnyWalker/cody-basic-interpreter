from cody_interpreter import IO
from cody_charset import CHARSET
from typing import Iterable
import queue
import threading


class CodyComputer:
    """
    A basic representation of the Cody Computer
    for use with the Cody BASIC interpreter's IO.
    """

    def __init__(self):
        self.__memory = bytearray(0x10000)

        # load charset into ROM
        assert len(CHARSET) == 0x800
        self.__memory[0xE000:0xE800] = CHARSET
        # cody basic at 0xE800

        self._init_mem()

    def _init_mem(self):
        """
        Write bytes into RAM to create the same state as the Cody BASIC interpreter after startup.
        """

        # set character memory
        self.memset_from(0xC800, self.memget_multi(0xE000, 0x800))

        # vid registers
        self.vid_scrl = 0
        self.vid_cntl = 0
        self.vid_border_color = 0x7  # yellow border
        self.vid_color_memory = 0xE  # 0xA000 + 14*0x400 = 0xD800
        self.vid_character_memory = 0x5  # 0xA000 + 5*0x800 = 0xC800
        self.vid_screen_memory = 0x9  # 0xA000 + 9*0x400 = 0xC400

        self.cursor_attr = 0x16  # white on blue
        # input prompt
        self.prompt = ord("?")

        # and clear the screen
        self.clear_screen()

    def clear_screen(self):
        self.cursor_col = 0
        self.cursor_row = 0
        self.tab_pos = 0

        # fill screen with spaces...
        self.memset_from(0xC400, [0x20] * 1000)
        # ...of the cursor color
        self.memset_from(0xD800, [self.cursor_attr] * 1000)

    def memget(self, address: int, width: int = 1) -> int:
        if width == 1:
            return self.__memory[address]
        else:
            result = 0
            for i in range(width):
                result |= self.__memory[address + i] << (8 * i)
            return result

    def memget_multi(self, address: int, length: int) -> bytearray:
        return self.__memory[address : address + length]

    def memset(self, address: int, value: int, width: int = 1):
        if address + width > 0xE000:
            raise ValueError("cannot write into ROM")
        if width == 1:
            self.__memory[address] = value
        else:
            for i in range(width):
                self.__memory[address + i] = value & 0xFF
                value >>= 8

    def memset_from(self, address: int, source: Iterable[int]):
        try:
            l = len(source)
        except TypeError:
            l = None

        if l is None:
            for i, value in enumerate(source):
                if address + i > 0xE000:
                    raise ValueError("cannot write into ROM")
                self.__memory[address + i] = value
        else:
            if address + l > 0xE000:
                raise ValueError("cannot write into ROM")
            self.__memory[address : address + l] = source

    class memprop:
        def __init__(self, address: int, *, width: int = 1, mask: int = -1):
            assert 0 <= address < 0x10000
            self.address = address

            assert width > 0
            self.width = width

            if mask == -1:
                mask = (1 << (8 * width)) - 1
            assert 0 < mask < (1 << (8 * width))
            self.mask = mask

            # find trailing zeros
            shift = 0
            while mask & 0b1 == 0:
                mask >>= 1
                shift += 1
            assert 0 <= shift < 8 * width
            self.shift: int = shift

            # assert there are no gaps in the mask
            while mask & 0b1 == 1:
                mask >>= 1
            assert mask == 0

        def __get__(self, instance: "CodyComputer", owner=None) -> int:
            masked = instance.memget(self.address, width=self.width) & self.mask
            return masked >> self.shift

        def __set__(self, instance: "CodyComputer", value: int):
            masked = (value << self.shift) & self.mask
            without_mask = instance.memget(self.address, width=self.width) & ~self.mask
            instance.memset(self.address, without_mask | masked, width=self.width)

    ### cody basic zero page ###

    sys_a = memprop(0x0000)
    sys_x = memprop(0x0001)
    sys_y = memprop(0x0002)
    jiffies = memprop(0x0006, width=2)
    isrptr = memprop(0x0008, width=2)
    prompt = memprop(0x000E)
    keyboard_row_0 = memprop(0x0010)
    keyboard_row_1 = memprop(0x0011)
    keyboard_row_2 = memprop(0x0012)
    keyboard_row_3 = memprop(0x0013)
    keyboard_row_4 = memprop(0x0014)
    keyboard_row_5 = memprop(0x0015)
    joystick_1 = memprop(0x0016)
    joystick_2 = memprop(0x0017)
    key_debounce = memprop(0x0018)
    key_last = memprop(0x0019)
    key_lock = memprop(0x001A)
    key_mods = memprop(0x001B)
    key_code = memprop(0x001C)
    cursor_attr = memprop(0x0037)
    cursor_attr_bg = memprop(0x0037, mask=0x0F)
    cursor_attr_fg = memprop(0x0037, mask=0xF0)
    cursor_col = memprop(0x0038)
    cursor_row = memprop(0x0039)
    tab_pos = memprop(0x000D)

    ### vid registers ###

    # blanking register
    vid_blnk = memprop(0xD000)

    # control register
    vid_cntl = memprop(0xD001)
    vid_screen_disable = memprop(0xD001, mask=0b0000_0001)
    vid_vertical_scroll_enable = memprop(0xD001, mask=0b0000_0010)
    vid_horizontal_scroll_enable = memprop(0xD001, mask=0b0000_0100)
    vid_row_effects_enable = memprop(0xD001, mask=0b0000_1000)
    vid_bitmap_enable = memprop(0xD001, mask=0b0001_0000)

    # color register
    vid_colr = memprop(0xD002)
    vid_border_color = memprop(0xD002, mask=0x0F)
    vid_color_memory = memprop(0xD002, mask=0xF0)

    # base register
    vid_bptr = memprop(0xD003)
    vid_character_memory = memprop(0xD003, mask=0x0F)
    vid_screen_memory = memprop(0xD003, mask=0xF0)

    # scroll register
    vid_scrl = memprop(0xD004)
    vid_vertical_scroll = memprop(0xD004, mask=0x0F)
    vid_horizontal_scroll = memprop(0xD004, mask=0xF0)

    # screen color register
    vid_scrc = memprop(0xD005)
    vid_color_2 = memprop(0xD005, mask=0x0F)
    vid_color_3 = memprop(0xD005, mask=0xF0)

    # sprite register
    vid_sprc = memprop(0xD006)
    vid_sprite_color = memprop(0xD006, mask=0x0F)
    vid_sprite_bank = memprop(0xD006, mask=0xF0)


class CodyIO(IO):
    def __init__(self, cody: CodyComputer):
        super().__init__()
        self.cody = cody
        self.cancel = False
        self.input_lock = threading.RLock()
        self.input_buffer = None
        self.input_queue = queue.Queue(1)

    def print_char(self, c: str, increment_cursor: bool = True):
        if self.uart is not None or self.bit_rate is not None:
            raise NotImplementedError("printing to uart not supported")
        offset = self.cody.cursor_row * 40 + self.cody.cursor_col
        self.cody.memset(0xC400 + offset, ord(c))
        self.cody.memset(0xD800 + offset, self.cody.cursor_attr)
        if increment_cursor:
            self.cody.cursor_col += 1
            if self.cody.cursor_col >= 40:
                self.cody.cursor_col = 0
                self.cody.cursor_row += 1
            if self.cody.cursor_row >= 25:
                self.cody.cursor_col = 0
                self.cody.cursor_row = 24
                # scroll up one row
                for y in range(24):
                    self.cody.memset_from(
                        0xC400 + y * 40,
                        self.cody.memget_multi(0xC400 + (y + 1) * 40, 40),
                    )
                    self.cody.memset_from(
                        0xD800 + y * 40,
                        self.cody.memget_multi(0xD800 + (y + 1) * 40, 40),
                    )
                # fill new row with spaces
                self.cody.memset_from(0xC400 + 24 * 40, [0x20] * 40)
                self.cody.memset_from(0xD800 + 24 * 40, [self.cody.cursor_attr] * 40)

    def println(self, value: str = ""):
        if self.uart is not None or self.bit_rate is not None:
            raise NotImplementedError("printing to uart not supported")
        self.print(value)
        # use auto linewrap/scrolling from print_char
        for _ in range(self.cody.cursor_col, 40):
            self.print_char(" ")

    def clear_screen(self):
        self.cody.clear_screen()

    def reverse_field(self):
        # switch foreground and background colors
        self.cody.cursor_attr_bg, self.cody.cursor_attr_fg = (
            self.cody.cursor_attr_fg,
            self.cody.cursor_attr_bg,
        )

    def set_background_color(self, c: int):
        self.cody.cursor_attr_bg = c

    def set_foreground_color(self, c: int):
        self.cody.cursor_attr_fg = c

    def print_at(self, col: int, row: int):
        self.cody.cursor_col = col
        self.cody.cursor_row = row

    def print_tab(self, col: int):
        raise NotImplementedError  # TODO

    def on_key_typed(self, c: str):
        """
        called from pygame code to add text to buffer
        """
        with self.input_lock:
            buf = self.input_buffer
            if buf is None and c == "\x18":  # cancel
                self.input_buffer = None
                self.cancel = True
                return

        if buf is not None:
            # buffer not None, other thread is waiting for the queue
            assert self.input_queue.qsize() == 0
            if c == "\n":
                self.println()
                self.input_buffer = None
                self.input_queue.put_nowait(buf)
            elif c == "\b":  # backspace
                if buf:
                    self.print_char(" ", increment_cursor=False)  # delete cursor
                    self.cody.cursor_col -= 1
                    self.print_char(" ", increment_cursor=False)  # clear previous char
                    self.input_buffer = buf[:-1]
            else:
                self.print_char(c)
                self.input_buffer = buf + c

        with self.input_lock:
            pass

    def blink(self, force_off: bool = False):
        """
        called from pygame code to blink the cursor
        """
        with self.input_lock:
            buf = self.input_buffer

        if buf is not None:
            # input is happening, we may blink
            swap = (self.cody.jiffies & 0x40) == 0
            if swap:
                self.reverse_field()
            self.print_char(" ", increment_cursor=False)
            if swap:
                self.reverse_field()

    def input(self, prompt: str) -> str:
        if self.uart is not None or self.bit_rate is not None:
            raise NotImplementedError("reading from uart not supported")
        self.print(prompt)
        with self.input_lock:
            assert self.input_buffer is None
            self.input_buffer = ""
        return self.input_queue.get()

    def prompt_char(self) -> str:
        return chr(self.cody.prompt)

    def peek(self, address: int) -> int:
        return self.cody.memget(address)

    def poke(self, address: int, value: int):
        self.cody.memset(address, value)

    def get_time(self) -> int | float | str:
        return self.cody.jiffies
