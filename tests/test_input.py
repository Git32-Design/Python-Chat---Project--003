import pygame
pygame.init()
screen = pygame.display.set_mode((400, 200))
font = pygame.font.Font(None, 36)
input_text = ""
active = True
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and active:
            if event.key == pygame.K_RETURN:
                print("输入内容:", input_text)
                input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode
    screen.fill((30,30,30))
    txt_surf = font.render(input_text, True, (255,255,255))
    screen.blit(txt_surf, (50,80))
    pygame.display.flip()
    clock.tick(60)
pygame.quit()