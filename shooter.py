#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 19:50:16 2024

@author: richiedadhley
"""

import pygame 
from pygame import mixer 
import os 
import random
import csv 
import button

# Initalise pygame and mixer 
mixer.init()
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter")

# Set framerate
clock = pygame.time.Clock()
FPS = 60

# Game variables 
GRAVITY = 0.65
SCROLL_THRESH = 200 # distance player gets to edge of screen before it scrolls
ROWS = 16 
COLS = 150 
TILE_SIZE = SCREEN_HEIGHT // ROWS 
TILE_TYPES = 21 
MAX_LEVELS = 3 # Update as you make more levels 
screen_scroll = 0 
bg_scroll = 0 
level = 1
start_game = False 
start_intro = False 

# Define player action variables
moving_left = False 
moving_right = False 
shoot = False 
grenade = False 
grenade_thrown = False 
head_size = 10 

# Load music and sounds 
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000) # -1 means loop forever, 0.0 is delay playing, 5000 = 5000ms fade in
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)

# Load Images
# button images
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
# Background images
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
# store tiles in a list 
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE,TILE_SIZE))
    img_list.append(img) 
# bullet and grenade
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
# Pick up boxes 
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health' : health_box_img,
    'Ammo' : ammo_box_img, 
    'Grenade' : grenade_box_img 
}


# Defining colours
BG = (144,201,120)
RED = (255,0,0)
WHITE = (255, 255, 255)
GREEN = (0,255,0)
BLACK = (0,0,0)
PINK = (235, 65, 54)

# Define font
font_size = 25
font = pygame.font.SysFont('Futura', font_size)

headshot_font = pygame.font.SysFont('Futura', 10)

def write_headshot(x,y):
    img = font.render("headshot", True, RED)
    screen.blit(img,(x,y))

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col) 
    screen.blit(img, (x,y))

def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5,0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6,SCREEN_HEIGHT - mountain_img.get_height()-300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

def reset_level():
    # start by emptying all the groups
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explostion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list 
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    
    return data 

class Solider(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self) 
        self.alive = True 
        self.char_type = char_type
        self.speed = speed 
        self.ammo = ammo
        self.start_ammo = ammo 
        self.shoot_cooldown = 0 
        self.grenades = grenades 
        self.health = 100 # Can give each person a different health by putting it as an argument and doing self.health = health 
        self.max_health = self.health
        self.headshot = False  
        self.direction = 1 
        self.vel_y = 0
        self.jump = False 
        self.in_air = True 
        self.flip = False 
        self.animation_list = []
        self.frame_index = 0
        self.action = 0 # 0 = idle, 1 = run 
        self.update_time = pygame.time.get_ticks()

        # AI specific variables 
        self.move_counter = 0
        self.vision = pygame.Rect(0,0, 150,20)
        self.idling = False 
        self.idling_counter = 0 

        # Load all images for players 
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            # Reset temporary list of images 
            temp_list = []
            # Count number of files in folder 
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))

            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)
            
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.COMx = self.rect.centerx - (10*self.direction)
        self.COMy = self.rect.centery + 15
        self.headx = self.rect.centerx - (3*self.direction) 
        self.heady = self.rect.centery - 13

    def update(self):
        self.update_animation()
        self.check_alive()

        # Update shooting cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1 

    def move(self, moving_left, moving_right):
        screen_scroll = 0 
        # Reset movement variables -- important when doing collision
        dx = 0 
        dy = 0 

        # Assign movement variables if moving left or right
        if moving_left:
            dx = - self.speed 
            self.flip = True 
            self.direction = -1
        if moving_right:
            dx = self.speed 
            self.flip = False 
            self.direction = 1
        
        # Jumping
        if self.jump == True and self.in_air == False:
            self.vel_y = -11 
            self.jump = False 
            self.in_air = True 

        # Applying gravity 
        self.vel_y += GRAVITY 
        if self.vel_y > 10: # setting a terminal velocity 
            self.vel_y = 10
        dy += self.vel_y 

        # Check for collision 
        for tile in world.obstacle_list:
			#check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
				#if the ai has hit a wall then make it turn around
                #if self.char_type == 'enemy':
                #    self.direction *= -1
                #    self.move_counter = 0

            # check collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below obstacle (i.e. jumping)
                if self.vel_y < 0: 
                    self.vel_y = 0 
                    dy = tile[1].bottom - self.rect.top # difference between head and bottom of obstacle
                # check if above obstacle (i.e. falling and standing)
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False # allows us to jump again 
                    dy = dy = tile[1].top - self.rect.bottom
        

        # check for collision with water 
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        # check for collision with exit 
        level_complete = False 
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True 

        # check if fallen off map 
        if self.rect.bottom > SCREEN_HEIGHT: 
            self.health = 0 

        # Check if going off edge of screen 
        if self.char_type == 'player': 
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0 
        
        # Update solider position
        self.rect.x += dx 
        self.rect.y += dy 
        self.COMx = self.rect.centerx - (10*self.direction)
        self.COMy = self.rect.centery + 15
        self.headx = self.rect.centerx - (3*self.direction) 
        self.heady = self.rect.centery - 13

        # update scroll based on player position 
        if self.char_type == 'player': # only the player can move the background
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                # make the player look like they're still while the background moves
                self.rect.x  -= dx 
                screen_scroll = -dx 
        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20 
            bullet = Bullet(self.rect.centerx + (self.rect.size[0])*0.75 * self.direction, self.rect.centery, self.direction)
            bullet_group.add(bullet)
            # Reduce ammo 
            self.ammo -= 1
            shot_fx.play()

    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1,200) == 1:
                self.update_action(0) # 0 is idle 
                self.idling = True 
                self.idling_counter = 50 

            # Check if the ai is near the player 
            if self.vision.colliderect(player.rect):
                # stop running and face player 
                self.update_action(0) # 0 is idle 
                #shoot
                self.shoot() 
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False 
                    ai_moving_left = not ai_moving_right 
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) # running animation 
                    self.move_counter += 1
                    # update vision as the enemy moves
                    self.vision.center = (self.rect.centerx + (75*self.direction), self.rect.centery)
                    #pygame.draw.rect(screen, RED, self.vision)

                    if self.move_counter > TILE_SIZE * 2:
                        self.direction *= -1 
                        self.move_counter *= -1 
                else: 
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False 

        # scroll 
        self.rect.x += screen_scroll      


    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 100
        # Update image depending on current frame 
        self.image = self.animation_list[self.action][self.frame_index]
        # Check if enough time has passed since last update 
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time  = pygame.time.get_ticks()
            self.frame_index += 1 
        # If the animation has run out, reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1 
            else:
                self.frame_index = 0
        if self.headshot == True:
            if pygame.time.get_ticks() - self.update_time < ANIMATION_COOLDOWN:
                write_headshot(self.headx - 30, self.heady -50)
            else:
                self.headshot = False 

    def update_action(self, new_action):
        # Check if the new action is different to the previous one 
        if new_action != self.action:
            self.action = new_action 
            # update the animation settings 
            self.frame_index = 0 
            self.update_time = pygame.time.get_ticks()


    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0 # Stop dead enemies floating around
            self.alive = False 
            self.update_action(3)

    def draw(self):
        # transform.flip flips the image in (x,y), i.e. self.flip will flip in x
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        #pygame.draw.circle(screen, WHITE, (self.COMx, self.COMy), TILE_SIZE*1.75)
        #pygame.draw.circle(screen, BLACK, (self.COMx, self.COMy), TILE_SIZE)
        #pygame.draw.circle(screen, RED, (self.headx, self.heady), head_size)

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # iterate through each value in level data file 
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0: 
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE 
                    img_rect.y = y * TILE_SIZE 
                    tile_data = (img, img_rect) 
                    if tile >= 0 and tile <= 8: # Dirt blocks
                        self.obstacle_list.append(tile_data)  
                    elif tile >= 9 and tile <=10: # Water tiles
                        water = Water(img, x*TILE_SIZE, y*TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14: # Decoration
                        decoration = Decoration(img, x*TILE_SIZE, y*TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15: # Player 
                        player = Solider('player', x*TILE_SIZE, y*TILE_SIZE, 1.65, 7, 20, 5)
                        health_bar = HealtBar(10,10, player.health, player.health)
                    elif tile == 16: # Enemy
                        enemy = Solider('enemy', x*TILE_SIZE, y*TILE_SIZE, 1.65, 2, 20, 0)
                        enemy_group.add(enemy)
                    elif tile == 17: # Ammo box
                        item_box = ItemBox('Ammo', x*TILE_SIZE, y*TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18: # Grendades  
                        item_box = ItemBox('Grenade', x*TILE_SIZE, y*TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19: # Health
                        item_box = ItemBox('Health', x*TILE_SIZE, y*TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20: # Exit
                        exit = Exit(img, x*TILE_SIZE, y*TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list: # tile is a tuple with tile[0] = image and tile[1] = posiiton
            tile[1][0] += screen_scroll # move the grid the world is built on as we scroll 
            screen.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img 
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img 
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img 
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type 
        self.image = item_boxes[self.item_type] 
        self.rect = self.image.get_rect()
        self.rect.midtop = (x+ TILE_SIZE//2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll
        # Check if the player has picked up the box 
        if pygame.sprite.collide_rect(self, player):
            # Check what kind of box it was 
            if self.item_type == 'Health':
                player.health += 25
                # Limit health to max_health
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            
            # Delete the item box
            self.kill()

class HealtBar():
    def __init__(self, x, y, health, max_health):
        self.x = x 
        self.y = y 
        self.health = health 
        self.max_health = max_health 

    def draw(self, health):
        # Update with new health 
        self.health = health 
        # Border for health bar
        pygame.draw.rect(screen, BLACK, (self.x-2, self.y-2, 154, 24))
        # Draw max health bar 
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        # Draw current health 
        ratio = self.health / self.max_health 
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y,direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10 
        self.image = bullet_img 
        self.rect = self.image.get_rect()
        self.rect.center = (x,y) 
        self.direction = direction
    
    def update(self):
        # Move the bullet 
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # Check if bullet has gone off screen 
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        
        # Check collisions
            
        # Collisions with walls 
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # Check for headshot on player
        distance_player_head = abs(((self.rect.centerx - player.headx)**2 + (self.rect.centery - player.heady)**2)**0.5)
        if distance_player_head < head_size: 
            if player.alive:
                player.health -= 25 
                player.headshot = True
                self.kill()
        # Bodyshot on player 
        elif pygame.sprite.spritecollide(player, bullet_group, False) and (self.rect.centery > (player.heady + 12)): # Checks for collision between a sprite and a group 
            if player.alive:
                player.health -= 5
                self.kill()

        for enemy in enemy_group:
            # Check for headshot on enemy 
            distance_enemy_head = abs(((self.rect.centerx - enemy.headx)**2 + (self.rect.centery - enemy.heady)**2)**0.5)
            if distance_enemy_head < head_size: 
                if enemy.alive:
                    enemy.health -= 100
                    enemy.headshot = True
                    self.kill()
        

            # Bodyshot on enemy 
            elif pygame.sprite.spritecollide(enemy, bullet_group, False) and (self.rect.centery > (enemy.heady + 12)): # Checks for collision between a sprite and a group 
                if enemy.alive: # Important as dont want bullets to be stopped by rect of dead enemies 
                    enemy.health -= 25 
                    self.kill()

class Grenade(pygame.sprite.Sprite):
    def __init__(self,x,y,direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100 
        self.vel_y = -11 
        self.speed = 7
        self.image = grenade_img 
        self.rect = self.image.get_rect()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect.center = (x,y) 
        self.direction = direction 
    
    def update(self):
        self.vel_y += GRAVITY 
        dx = self.direction * self.speed 
        dy = self.vel_y 

        # Check for collision with level 
        for tile in world.obstacle_list:
            # Check for collision with walls 
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1 
                dx = self.direction * self.speed

            # Check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below obstacle (i.e. thrown up)
                self.speed = 0
                if self.vel_y < 0: 
                    self.vel_y = 0 
                    dy = tile[1].bottom - self.rect.top # difference between head and bottom of obstacle
                # check if above obstacle (i.e. falling)
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = dy = tile[1].top - self.rect.bottom
        
        # Check collision with walls: bounces off them 
        if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
            self.direction *= -1 
            dx = self.direction * self.speed 

        # Update position 
        self.rect.x += dx + screen_scroll
        self.rect.y += dy 

        # Countdown timer
        self.timer -= 1 
        if self.timer <= 0:
            grenade_fx.play()
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 0.8)
            explostion_group.add(explosion)

            # Do damage to anyone that is near by EDIT LATER TO GIVE MULTIPLE RADII
            if player.alive:
                distance_player = ((self.rect.centerx - player.COMx)**2 + (self.rect.centery - player.COMy)**2)**0.5
                if distance_player < TILE_SIZE:
                    player.health -= 75
                elif distance_player < TILE_SIZE * 1.75:
                    player.health -= 25

            for enemy in enemy_group:
                if enemy.alive:
                    distance_enemy = ((self.rect.centerx - enemy.COMx)**2 + (self.rect.centery - enemy.COMy)**2)**0.5
                    if distance_enemy < TILE_SIZE:
                        enemy.health -= 75
                    elif distance_enemy < TILE_SIZE * 1.75:
                        enemy.health -= 25
               
class Explosion(pygame.sprite.Sprite):
    def __init__(self,x,y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1,6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0 
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.counter = 0 

    def update(self):
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4 
        # Update explosion animation 
        self.counter += 1 
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0 
            self.frame_index += 1 
            # Check if animation is complete and delete explosion 
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction 
        self.colour = colour 
        self.speed = speed 
        self.fade_counter = 0 
    
    def fade(self):
        # Create a rectangle that moves down the screen at self.speed 
        fade_complete = False 
        self.fade_counter += self.speed

        if self.direction == 1: # Whole screen fade 
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH//2 , SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH//2 + self.fade_counter, 0, SCREEN_WIDTH//2 , SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH , SCREEN_HEIGHT//2))
            pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT//2 + self.fade_counter, SCREEN_WIDTH , SCREEN_HEIGHT//2))

        if self.direction == 2: # vertical screen fade down 
            pygame.draw.rect(screen, self.colour, (0,0, SCREEN_WIDTH, 0 + self.fade_counter))

            # Check is screen completely filled 
        if self.fade_counter >= SCREEN_WIDTH: # This is not an exact number, just know that its sufficient!
            fade_complete = True 

        return fade_complete
    
# create screen fades 
intro_fade = ScreenFade(1, BLACK, 4) 
death_fade = ScreenFade(2, PINK, 4)

# Create buttons 
start_button = button.Button(SCREEN_WIDTH//2 - 130, SCREEN_HEIGHT //2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT //2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT //2 - 50, restart_img, 2)

# Create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explostion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# Create empty tile list 
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)

# load in level data and create world 
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader= csv.reader(csvfile, delimiter=',')
    for x,row in enumerate(reader):
        for y,tile in enumerate(row):
            world_data[x][y] = int(tile) 

# Create the world
world = World()
# Set the player and health bar to the world data
player, health_bar = world.process_data(world_data)

run = True 
while run:
    
    clock.tick(FPS)

    if start_game == False:
        # draw main menu 
        screen.fill(BG) 
        # add buttons 
        if start_button.draw(screen):
            start_game = True 
            start_intro = True 
        elif exit_button.draw(screen):
            run = False 
    
    else:
        # Update the background
        draw_bg()
        # Draw world map
        world.draw()

        # Show player Health
        health_bar.draw(player.health) 

        # Show Ammo and Grenades 
        draw_text('AMMO: ', font, WHITE, 10, 30)
        for x in range(player.ammo):
            screen.blit(bullet_img, (110 + (x * 10), 30+ font_size//2))
        draw_text('GRENADES: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (160 + (x * 15), 60 + font_size //2 ))

        # Update and draw groups
        bullet_group.update()
        bullet_group.draw(screen)

        grenade_group.update()
        grenade_group.draw(screen) 

        explostion_group.update()
        explostion_group.draw(screen)   

        item_box_group.update()
        item_box_group.draw(screen)

        decoration_group.update()
        decoration_group.draw(screen)

        water_group.update()
        water_group.draw(screen)

        exit_group.update()
        exit_group.draw(screen)

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        player.update()
        player.draw()

        # show intro
        if start_intro:
            if intro_fade.fade():
                start_intro = False 
                intro_fade.fade_counter = 0 

        # Update player actions 
        if player.alive:
            # Shoot bullets: create function for Solider as both player and enemies will be able to shoot 
            if shoot: 
                player.shoot()
            # Throw grenade: don't need to make a function for Solider as only player will be able to throw grenades 
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (player.rect.size[0] * 0.5 + player.direction),\
                                player.rect.top, player.direction) 
                grenade_group.add(grenade)
                player.grenades -= 1
                grenade_thrown = True 

            if player.in_air: 
                player.update_action(2) # Jumping  
            elif moving_left or moving_right: 
                player.update_action(1) # They are running
            else: 
                player.update_action(0) # They are idle 

            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll

            # check if player has completed the level 
            if level_complete:
                start_intro = True 
                level += 1 
                bg_scroll = 0 
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader= csv.reader(csvfile, delimiter=',')
                        for x,row in enumerate(reader):
                            for y,tile in enumerate(row):
                                world_data[x][y] = int(tile) 

                    # Create the world
                    world = World()
                    # Set the player and health bar to the world data
                    player, health_bar = world.process_data(world_data)
        
        else: 
            screen_scroll = 0 
            if death_fade.fade():
                if restart_button.draw(screen): # when restart button clicked after dying, need to reset level
                    death_fade.fade_counter = 0 # reset so that it runs every time you die 
                    start_intro = True 
                    bg_scroll = 0 
                    world_data = reset_level() # empties all groups and sets world data back to blank spaces (i.e. -1 everywhere)

                    # load in level data and create world 
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader= csv.reader(csvfile, delimiter=',')
                        for x,row in enumerate(reader):
                            for y,tile in enumerate(row):
                                world_data[x][y] = int(tile) 

                    # Create the world
                    world = World()
                    # Set the player and health bar to the world data
                    player, health_bar = world.process_data(world_data)


    
    for event in pygame.event.get():
        # This is for quitting the game, i.e. clicking red cross exits the code
        if event.type == pygame.QUIT:
            run = False

        # Any keyboard button pressed 
        if event.type == pygame.KEYDOWN:

            # Can use esc key to exit game 
            if event.key == pygame.K_ESCAPE:
                run = False 

            # Moving controls 
            if event.key == pygame.K_LEFT:
                moving_left = True
            if event.key == pygame.K_RIGHT:
                moving_right = True
            if event.key == pygame.K_UP and player.alive:
                player.jump = True
                jump_fx.play()
            
            # Spacebar for shooting
            if event.key == pygame.K_SPACE:
                shoot = True 
            # g for grenade 
            if event.key == pygame.K_g:
                grenade = True 

        # Any keyboard button released 
        if event.type == pygame.KEYUP: 

            # Moving controls 
            if event.key == pygame.K_LEFT:
                moving_left = False
            if event.key == pygame.K_RIGHT:
                moving_right = False

            # Space for shooting
            if event.key == pygame.K_SPACE:
                shoot = False
            # g for grenade 
            if event.key == pygame.K_g:
                grenade = False  
                grenade_thrown = False 

    pygame.display.update()


pygame.quit()