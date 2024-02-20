import pygame 
import button 
import csv 
import pickle 

pygame.init()

clock = pygame.time.Clock()
FPS = 60 

# game window 
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640 
LOWER_MARGAIN = 100 
SIDE_MARGAIN = 300 


screen = pygame.display.set_mode((SCREEN_WIDTH+SIDE_MARGAIN, SCREEN_HEIGHT+LOWER_MARGAIN))
pygame.display.set_caption('Level Editor')

# Define game variables 
ROWS = 16 
MAX_COLUMNS = 150 
TILE_SIZE = SCREEN_HEIGHT// ROWS 
TILE_TYPES = 21 
level = 0 
current_tile = 0 
scroll_left = False 
scroll_right = False 
scroll = 0 
scroll_speed = 1 

# Load images 
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
# Store tiles in a list 
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/tile/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)) # Make the images same size as a tile 
    img_list.append(img) 

save_img = pygame.image.load('img/save_btn.png').convert_alpha()
load_img = pygame.image.load('img/load_btn.png').convert_alpha()


# Define colours
GREEN = (144,201,120)
WHITE = (255,255,255)
RED = (200,25,25)

# define font 
font = pygame.font.SysFont('Futura', 20)

# Create empty tile list 
world_data = []
for row in range(ROWS):
    r = [-1] * MAX_COLUMNS 
    world_data.append(r)

# Create ground 
for tile in range(0,MAX_COLUMNS):
    world_data[ROWS-1][tile] = 0

# function for outputting text onto screen 
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col) 
    screen.blit(img, (x,y))


# Create function for drawing background 
def draw_bg():
    screen.fill(GREEN)
    width = sky_img.get_width() # All images have the same width, so can use any 
    # Build background in layors, repeat images for scrolling and multiplies to give 3D effect 
    for x in range(4): 
        screen.blit(sky_img, ((x*width)-scroll * 0.5, 0))
        screen.blit(mountain_img, ((x*width)-scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x*width)-scroll * 0.7, SCREEN_HEIGHT- pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x*width)-scroll * 0.8, SCREEN_HEIGHT- pine2_img.get_height()))

# drwa grid 
def draw_grid():
    # vertical lines 
    for c in range(MAX_COLUMNS+1):
        pygame.draw.line(screen, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, SCREEN_HEIGHT))
    # horizontal lines 
    for h in range(ROWS+1):
        pygame.draw.line(screen, WHITE, (0, h * TILE_SIZE), (SCREEN_WIDTH, h * TILE_SIZE))


# Function for drawing world tiles 
def draw_world():
    for y, row in enumerate(world_data):
        for x, tile in enumerate(row):
            if tile >= 0:
                screen.blit(img_list[tile], (x*TILE_SIZE - scroll, y*TILE_SIZE))

# create buttons
save_button = button.Button(SCREEN_WIDTH //2 , SCREEN_HEIGHT + LOWER_MARGAIN - 50, save_img, 1)
load_button = button.Button(SCREEN_WIDTH //2 +200, SCREEN_HEIGHT + LOWER_MARGAIN - 50, load_img, 1)
# Make a button list 
button_list = []
button_col = 0 
button_row = 0 
for i in range(len(img_list)):
    tile_button = button.Button(SCREEN_WIDTH + (75*button_col) +50, (75*button_row) + 50, img_list[i], 1)
    button_list.append(tile_button) 
    button_col += 1 
    if button_col == 3:
        button_row += 1
        button_col = 0 


run = True 
while run: 

    clock.tick(FPS)

    draw_bg()
    draw_grid()
    draw_world()

    draw_text(f'Level: {level}', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGAIN - 90)
    draw_text('Press UP or DOWN to change level', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGAIN - 60)
    
    # save and load data 
    if save_button.draw(screen):
        # Save level data 
        pickle_out = open(f'level{level}_data', 'wb')
        pickle.dump(world_data, pickle_out)
        pickle_out.close()

        # CSV method 
        #with open(f'level{level}_data.csv', 'w', newline='') as csvfile:
        #    writer = csv.writer(csvfile, delimiter=',')
        #    for row in world_data:
        #        writer.writerow(row) 

    if load_button.draw(screen):
        # load in level data 
        # reset scroll back to start of the level 
        scroll = 0 
        world_data = []
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
        
        # CSV method 
        #with open(f'level{level}_data.csv', newline='') as csvfile:
        #    reader = csv.reader(csvfile, delimiter=',')
        #    for x, row in enumerate(reader):
        #        for y, tile in enumerate(row):
        #            world_data[x][y] = int(tile)
                

    # Draw tile panel and tiles 
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH, 0, SIDE_MARGAIN, SCREEN_HEIGHT))
    # Select a tile 
    button_count = 0
    for button_count,i in enumerate(button_list):
        if i.draw(screen):
            current_tile = button_count 
        
    # highlight selected tile
    pygame.draw.rect(screen, RED, button_list[current_tile].rect, 3)

    # Scroll the map
    if scroll_left == True and scroll > 0: 
        scroll -= 5 * scroll_speed
    if scroll_right == True and scroll < (MAX_COLUMNS * TILE_SIZE) - SCREEN_WIDTH:
        scroll += 5 * scroll_speed 

    # Add new tiles to the screen 
    # get mouse position 
    pos = pygame.mouse.get_pos() 
    x = (pos[0]+ scroll) // TILE_SIZE
    y = (pos[1]) // TILE_SIZE

    # check that the coordinates are within the building area
    if pos[0] < SCREEN_WIDTH and pos[1] < SCREEN_HEIGHT:
        # update tile value
        if pygame.mouse.get_pressed()[0] == 1: # get_pressed[0] = left click
            if world_data[y][x] != current_tile:
                world_data[y][x] = current_tile 
        elif pygame.mouse.get_pressed()[2] == 1: # get_pressed[2] = right clicked
            world_data[y][x] = -1

    for event in pygame.event.get():
        # Keyboard presses 
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                level += 1 
            if event.key == pygame.K_DOWN and level > 0:
                level -= 1
            if event.key == pygame.K_LEFT:
                scroll_left = True 
            if event.key == pygame.K_RIGHT:
                scroll_right = True 
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 5

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                scroll_left = False
            if event.key == pygame.K_RIGHT:
                scroll_right = False  
            if event.key == pygame.K_RSHIFT:
                scroll_speed = 1


        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()