import pygame
pygame.init()
screen = pygame.display.set_mode((600, 337), pygame.RESIZABLE)
pygame.display.set_caption("Spiel")
icon = pygame.image.load('game/images/icon.png')
pygame.display.set_icon(icon)
#Меню игры с названием в центре сверху центрированным и фоновой картинкой
#Кнопки старта, загрузки, настроек и выхода из игры



myfont = pygame.font.Font("game/fonts/Merri.ttf", 80)
text_surface = myfont.render("Start", True, "Red")
background = pygame.image.load('game/images/background.png')

running = True
while running:
    
    screen.blit(background, (0, 0))
    pygame.display.update()
    
     
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                screen.fill((69, 62, 201))
                
    pygame.display.flip()