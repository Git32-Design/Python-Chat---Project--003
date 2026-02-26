import pygame
pygame.init()
screen = pygame.display.set_mode((400, 300))
screen.fill((255, 0, 0))  # 红色背景
pygame.display.flip()
import time
time.sleep(3)  # 停留3秒
pygame.quit()