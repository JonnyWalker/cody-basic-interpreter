import pygame


def main():
    # pygame setup
    pygame.init()

    # 40 cols, 4 horizontal pixels
    # 25 rows, 8 vertical pixels
    w, h = 160, 200
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

        # TODO: render based on contents of cody memory
        screen.fill("yellow")
        pygame.draw.circle(screen, "red", (w / 2, h / 2), 50, 1)

        # flip() the display to put your work on screen
        pygame.display.flip()
        clock.tick(60)  # limits FPS to 60

    pygame.quit()


if __name__ == "__main__":
    main()
