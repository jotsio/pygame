import pygame
#import sys, pygame
import pygame.gfxdraw
from pygame.locals import *
import random
import time
from inits import *
from levels import *
from classes import *


# Show game titles
def showText(message):
    font = pygame.font.Font('freesansbold.ttf', 48) 
    text = font.render(message, True, color_text)
    textRect = text.get_rect()
    textRect.center = (width // 2, height // 2)
    SCREEN.blit(text, textRect)
    pygame.display.flip()

def showScore(number):
    font = pygame.font.Font('freesansbold.ttf', 32) 
    text = font.render(number, True, color_text)
    textRect = text.get_rect()
    textRect.center = (width - 64, height - 64)
    SCREEN.blit(text, textRect)
    pygame.display.flip()

def showHearts(amount):
    image = GR_UI_HEART_DEFAULT
    Rect = image[0].get_rect()
    Rect.y = height - Rect.height
    Rect.x = 0
    i = 0
    while i < amount:
        SCREEN.blit(image[0], Rect)
        Rect.x += Rect.width
        i += 1

# CLASSES
# -------
# Enemy class
class NewEnemy(pygame.sprite.Sprite, AnimObject):
    def __init__(self, x, y, features):
        pygame.sprite.Sprite.__init__(self)
        AnimObject.__init__(self, features["image_default"])
        global enemy_ammo_group
        enemy_group.add(self)
        self.image_default = features["image_default"]
        self.image = self.image_default[0]
        self.animation = features["animation_blink"]
        self.animation_frame = 0
        self.rect = self.image.get_rect() 
        self.rect = self.rect.move(x, y)
        self.hitbox = self.rect
        self.hit_points = features["hit_points"]
        self.shoot_delay = features["shoot_delay"]
        self.blinking = False
        self.animation_frame = 0
        self.animation_delay = 4
        self.animation_counter = 0
        self.hor_margin = -8
        self.ver_margin = -8
        self.speedx, self.speedy = features["initial_speed"]
        self.counter = 0
        self.last_shoot = self.counter
        self.type = features["type"]
        self.score = features["score"]
        self.accuracy = 16

    # Passive movement & collision detection
    def update(self, level, offset):
        global boss_alive
        global score
        # Check if dead
        if self.hit_points <= 0:
            snd_enemy_death.play()
            NewEffect(self.rect.centerx, self.rect.centery, GR_EFFECT_EXPLOSION_BIG)
            if self.type == "Boss":
                
                boss_alive = False
            score += self.score
            self.kill()

        # Check if outside area
        if self.rect.y < -gridsize * 2 or self.rect.y > height:
            self.kill()

        # Blinking
        if self.blinking == True:
            if self.animation_frame == len(self.animation):
                self.animation_frame = 0
                self.image = self.image_default[0]
                self.animation_counter = 0
                self.blinking = False
            else:
                self.image = self.animation[self.animation_frame]
                if self.animation_counter == self.animation_delay:
                    self.animation_frame += 1
                    self.animation_counter = 0
                self.animation_counter +=1

        # Check collision ammo
        if pygame.sprite.spritecollideany(self, player_ammo_group, collided):
            self.hit_points -= 1
            self.blinking = True

        # Check collision to player
        if pygame.sprite.spritecollideany(self, player_group, collided):
            self.hit_points = 0

        # Check collision to walls
        if level.checkCollision(self.hitbox, offset) or self.rect.left <= 0 or self.rect.right >= width:
            self.speedx = -self.speedx

        # Check shooting delay
        if self.counter - self.last_shoot > self.shoot_delay and abs(player.rect.centerx - self.rect.centerx) < self.accuracy:
            self.shoot()
            self.last_shoot = self.counter
        
        self.counter += 1

    def move(self, scroll_speed):
        # Keep on scrolling
        self.rect = self.rect.move(self.speedx, self.speedy)
        self.rect = self.rect.move(0, round(scroll_speed))
        self.resetHitbox()
        
    def resetHitbox(self):
        # Align hitbox
        self.hitbox = self.rect
        self.hitbox = self.hitbox.inflate(self.hor_margin, self.ver_margin)

    # Shooting
    def shoot(self):
        AmmoSingle(self.rect.centerx, self.rect.bottom, feat_enemy_beam_default)
        self.shoot_timer = 0 

# Player class
class PlayerShip(pygame.sprite.Sprite, AnimObject):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        AnimObject.__init__(self, imageset = GR_PLAYER_BODY_DEFAULT)
        self.imageset_hilight = GR_PLAYER_BODY_BLINK
        self.imageset_up = GR_PLAYER_BODY_UP 
        self.start_x = x
        self.start_y = y
        self.alive = True
        self.hit_points = 5
        self.hit_points_max = 6
        self.speedx = 0.0
        self.speedy = 0.0
        self.hor_margin = -15
        self.ver_margin = -30
        self.max_speedx = 4.0
        self.max_speedy = 2.0
        self.frictionX = 0.2 
        self.frictionY = 0.2
        self.setStartPosition()
        self.weapon = WeaponDefault()
        player_group.add(self)
    
    # Set player to starting position on screen and initialize hitbox
    def setStartPosition(self):
        self.rect.x = 0
        self.rect.y = 0
        self.rect = self.rect.move(self.start_x, self.start_y)
        self.resetHitbox()
        
    # Passive movement & collision detection
    def update(self, level, offset):
        # Check if dead
        if self.hit_points <= 0:
            self.alive = False
            snd_player_death.play()
            player_group.remove(player)
            NewEffect(self.rect.centerx, self.rect.centery, GR_EFFECT_EXPLOSION_BIG)

        # Check collision to walls
        if self.alive == True and level.checkCollision(self.hitbox, offset):
            self.hit_points = 0

        # Check collision to ammo
        if self.alive == True and pygame.sprite.spritecollideany(self, enemy_ammo_group, collided):
            self.hit_points -= 1
            self.setAnimation(self.imageset_hilight, 12)

        # Check collision to enemy
        if pygame.sprite.spritecollideany(self, enemy_group, collided):
            self.hit_points = 0

        # Update shooting delay
        self.weapon.shoot_timer += 1

        # bounces from outside the area
        if self.rect.left < 0:
            self.rect.left = 0
            self.speedx = -self.speedx
        if self.rect.right > width:
            self.rect.right = width
            self.speedx = -self.speedx
        if self.rect.top < 0:
            self.rect.top = 0
            self.speedy = -self.speedy
        if self.rect.bottom > height:
            self.rect.bottom = height
            self.speedy = -self.speedy

        # Horizontal friction
        if self.speedx > 0 :
            self.speedx -= self.frictionX
        if self.speedx < 0 :
            self.speedx += self.frictionX

        # Vertical friction
        if self.speedy > 0 :
            self.speedy -= self.frictionY
        if self.speedy < 0 :
            self.speedy += self.frictionY
        
        # Set thruster animation if moved
        if self.speedy < -1.0:
            self.setAnimation(self.imageset_up, 4)

        # Change animation frame
        self.changeFrame()

        # Ensures that hitbox is following
        self.resetHitbox()


    def move(self, scroll_speed): 
        # Move the player
        self.rect = self.rect.move(round(self.speedx), round(self.speedy))
        self.resetHitbox()
        
    def resetHitbox(self):
        # Align hitbox
        self.hitbox = self.rect
        self.hitbox = self.hitbox.inflate(self.hor_margin, self.ver_margin)

    # Vertical acceleration
    def setSpeedX(self, amount):
        self.speedx += amount
        if self.speedx > self.max_speedx :
            self.speedx = self.max_speedx
        if self.speedx < -self.max_speedx :
            self.speedx = -self.max_speedx

    # Horizontal acceleration
    def setSpeedY(self, amount):
        self.speedy += amount
        if self.speedy > self.max_speedy :
            self.speedy = self.max_speedy
        if self.speedy < -self.max_speedy :
            self.speedy = -self.max_speedy

    # Change a weapon
    def changeWeapon(self, key):
        if key[pygame.K_1] == True:
            self.weapon = WeaponDefault()
        if key[pygame.K_2] == True:
            self.weapon = WeaponDoubleBeam()
        if key[pygame.K_3] == True:
            self.weapon = WeaponMinigun()
        if key[pygame.K_4] == True:
            self.weapon = WeaponFlameThrower()

    # Shooting
    def shoot(self, key):
        if self.alive == True and key == True:
            self.weapon.launch(self.rect.centerx, self.rect.y)

class WeaponDefault():
    def __init__(self):
        self.shoot_timer = 0
        self.shoot_delay = 16

    def launch(self, x, y):
        if self.shoot_timer >= self.shoot_delay:
            AmmoSingle(x, y, feat_player_beam_default)
            self.shoot_timer = 0 

class WeaponDoubleBeam():
    def __init__(self):
        self.shoot_timer = 0
        self.shoot_delay = 24

    def launch(self, x, y):
        if self.shoot_timer >= self.shoot_delay:
            AmmoSingle(x - 16, y, feat_player_beam_default)
            AmmoSingle(x + 16, y, feat_player_beam_default)
            self.shoot_timer = 0 

class WeaponMinigun():
    def __init__(self):
        self.shoot_timer = 0
        self.shoot_delay = 4

    def launch(self, x, y):
        if self.shoot_timer >= self.shoot_delay:
            AmmoSingle(x, y, feat_player_beam_default)
            self.shoot_timer = 0 

class WeaponFlameThrower():
    def __init__(self):
        self.shoot_timer = 0
        self.shoot_delay = 4

    def launch(self, x, y):
        if self.shoot_timer >= self.shoot_delay:
            AmmoSingle(x, y, feat_player_flame)
            self.shoot_timer = 0 

def selectEnemy(x, y, character):
    if character == "X": 
#        return EnemyFighter()
        return NewEnemy(x, y, enemy_types_list[0])
    elif character == "O":
#        return EnemySpike()
        return NewEnemy(x, y, enemy_types_list[1])
    elif character == "Z":    
#        return EnemyFighterBig()
        return NewEnemy(x, y, enemy_types_list[2])

# Main program
#-------------
# Pygame initials

# Title
pygame.display.set_caption("Luolalentely")
icon = GR_PLAYER_BODY_DEFAULT
pygame.display.set_icon(icon[0])

# Create player
player = PlayerShip(player_start_x, player_start_y)

# Main loop
while True: 
    # Play the level
    offset = 0
    scroll_speed = basic_scroll_speed
    end_counter = 0
    stars = StarField(250)
    this_level = levels[current_level]
    clock = pygame.time.Clock()
    pygame.mixer.music.play(-1)
    boss_alive = True
    
    while clock.tick(framerate):
        # Keyevents listener
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()

        pressed = pygame.key.get_pressed()
        player.setSpeedX(pressed[pygame.K_RIGHT]-pressed[pygame.K_LEFT])
        player.setSpeedY(pressed[pygame.K_DOWN]-pressed[pygame.K_UP])
        player.shoot(pressed[pygame.K_SPACE])
        player.changeWeapon(pressed)
         
       # Is player alive?
        if player.alive == False:
            player.speedx = 0.0
            player.speedy = 0.0
            if end_counter > framerate:
                break
            end_counter += 1

        # Is player reached the end of level?
        if offset == -this_level.start_point:
            scroll_speed = 0  

        # Check if boss is dead         
        if boss_alive == False:
            if end_counter > framerate * 2:
                break
            end_counter += 1

        # Objects update
        player_group.update(this_level, offset)
        enemy_group.update(this_level, offset)
        player_ammo_group.update(this_level, offset)
        enemy_ammo_group.update(this_level, offset)
        effects_group.update(this_level, offset)

        # Objects movement
        for i in player_group.sprites():
            i.move(scroll_speed)

        for i in enemy_group.sprites():
            i.move(scroll_speed)

        for i in player_ammo_group.sprites():
            i.move(scroll_speed)

        for i in enemy_ammo_group.sprites():
            i.move(scroll_speed)

        for i in effects_group.sprites():
            i.move(scroll_speed)

        # Create enemies
        enemy_positions_list = this_level.getEnemies(offset)
        if enemy_positions_list:
            for i in enemy_positions_list:
                enemy = selectEnemy(i[0], i[1], i[2])

        # Background update
        SCREEN.fill(color_bg_default)
        stars.draw(SCREEN, 2)
        this_level.draw(offset, SCREEN)        

        # Draw all the objects
        player_group.draw(SCREEN)
        enemy_group.draw(SCREEN)
        player_ammo_group.draw(SCREEN)
        enemy_ammo_group.draw(SCREEN)
        effects_group.draw(SCREEN)
        # Rectange for collision debugging
        #pygame.draw.rect(SCREEN, RED, player.hitbox, 1)

        # Show hearts of hitpoints
        showHearts(player.hit_points)

        # Show score
        showScore(str(score))

        # Update screen
        pygame.display.flip()
        
        # Move the whole screen up one step
        offset += scroll_speed

    # Show level ending text
    if player.alive == False:
        showText("Kuolit!")
        # Reset player
        player = PlayerShip(player_start_x, player_start_y)
        enemy_group.empty()
        player_ammo_group.empty()
        enemy_ammo_group.empty()
        effects_group.empty()
        
    elif current_level == (len(levels)-1):
        showText("HIENOA, PELI LÄPÄISTY!")
        player.setStartPosition()
        current_level = 0
    else:
        showText("Kenttä läpäisty!")
        player.setStartPosition()
        boss_alive = True
        current_level += 1  

    pygame.event.clear()
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            pygame.QUIT()
            sys.exit()
        if event.type == KEYDOWN and event.key == K_RETURN:
            break




