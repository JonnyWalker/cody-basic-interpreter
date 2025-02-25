import pygame
from cody_computer import CodyComputer, CodyIO

COLORS = [
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
    "lightred",
    "darkgray",
    "gray",
    "lightgreen",
    "lightblue",
    "lightgray",
]

BORDER_TOP = 8
BORDER_LEFT = 4


def render(s: pygame.Surface, cmp: CodyComputer):
    color_memory = 0xA000 + 0x400 * cmp.vid_color_memory
    character_memory = 0xA000 + 0x800 * cmp.vid_character_memory
    screen_memory = 0xA000 + 0x400 * cmp.vid_screen_memory

    border_color = COLORS[cmp.vid_border_color]
    s.fill(border_color)

    for i in range(1000):
        x, y = i % 40, i // 40
        char_index = cmp.memget(screen_memory + i)
        for yy in range(8):
            char_row_data = cmp.memget(character_memory + 8 * char_index + yy)
            for xx in range(4):
                char_data = (char_row_data >> (2 * (3 - xx))) & 0b11
                if char_data == 0:
                    color_index = cmp.memget(color_memory + i) & 0xF
                elif char_data == 1:
                    color_index = (cmp.memget(color_memory + i) >> 4) & 0xF
                elif char_data == 2:
                    color_index = cmp.cursor_attr_bg
                elif char_data == 3:
                    color_index = cmp.cursor_attr_bg

                color = COLORS[color_index]
                s.set_at((BORDER_LEFT + x * 4 + xx, BORDER_TOP + y * 8 + yy), color)


def start(cmp: CodyComputer):
    # pygame setup
    pygame.init()

    # 40 cols, 4 horizontal pixels
    # 25 rows, 8 vertical pixels
    w, h = 160 + 2 * BORDER_LEFT, 200 + 2 * BORDER_TOP
    # SCALED makes the window not appear tiny on big screens
    flags = pygame.SCALED | pygame.RESIZABLE
    screen = pygame.display.set_mode((w, h), flags)

    clock = pygame.time.Clock()
    running = True

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        if not running:
            break  # insta-close

        render(screen, cmp)

        # flip() the display to put your work on screen
        pygame.display.flip()
        clock.tick(60)  # limits FPS to 60

    pygame.quit()


def main():
    cmp = CodyComputer()
    io = CodyIO(cmp)
    io.print("Hello World")
    start(cmp)


if __name__ == "__main__":
    main()
