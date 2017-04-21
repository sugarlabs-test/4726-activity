#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# SpaceWar
# Copyright (C) 2007
# Copyright (C) 2013, Alan Aguiar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact information:
# Alan Aguiar <alanjas@gmail.com>

import os
import gtk
import itertools
import pygame
import random

from gettext import gettext as _

POINTS_ENEMY = 1000
POINTS_SHOT = 100

class SpaceWar():
    """Top-level application class."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.count = 0
        self.level = 1
        self.points = 0
        self.old_points = 0
        self.running = True
        self.screen = None
        self._points_large = 250
        

    def get_stats(self):
        msg = str(self.level) + '\n'
        msg = msg + str(self.points)
        return msg

    def set_stats(self, stats):
        l = stats.split('\n')
        if len(l) == 2:
            self.level = int(l[0])
            self.points = int(l[1])

    def calc_points_large(self):
        msg = 9 * '0'
        points_msg = self._font.render(_('Score: %s') % msg, 1, (255, 255, 255))
        self._points_large = points_msg.get_width() + 10

    def load_all(self):
        # Dun dun duuuuuuuun
        pygame.display.init()
        
        # Initialize the screen surface
        self.screen = pygame.display.get_surface()
        if not(self.screen):
            info = pygame.display.Info()
            size = (info.current_w, info.current_h)
            self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
            pygame.display.set_caption(_('SpaceWar'))
        self.rect = self.screen.get_rect()

        # Core objects
        self.clock = pygame.time.Clock()
                
        # images
        self.ship_img = pygame.image.load('img/Space/ship1.png').convert_alpha()
        self.shot_img = pygame.image.load('img/Space/bullet4.png').convert_alpha()
        self.enemy_img = pygame.image.load('img/OldSchool/skully.png').convert_alpha()

        pygame.mixer.init()
        self.shot_sound = pygame.mixer.Sound('sounds/shot.wav')

        # game labels
        pygame.font.init()
        self._font = pygame.font.Font(None, 40)
        self.level_msg = self._font.render(_('Level: %s') % self.level, 1, (255, 255, 255))
        self.do_score_msg()

        # Game objects
        self.ship = Ship(self)
        self.ship.rect.midbottom = self.rect.midbottom
        self.shots = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        # Add enemies
        self.add_enemies(self.level)
        self.calc_points_large()

    def add_enemies(self, level):
        for l in range(level):
            enemy = Enemy(self)
            x = random.randint(0, self.rect[2])
            y = random.randint(50, self.rect[3] - 100)
            enemy.rect.center = x, y
            enemy.direction = random.choice((-1 , 1))
            self.enemies.add(enemy)

    def do_score_msg(self):
        if self.points < 0:
            p = str(abs(self.points))
            c =  (8 - len(p)) * '0'
            msg = '-' + c + p
        else:
            p = str(self.points)
            c =  (8 - len(p)) * '0'
            msg = c + p
        self.points_msg = self._font.render(_('Score: %s') % msg, 1, (255, 255, 255))

    def run(self):
        self.load_all()

        while self.running:
            # Timing phase
            delta = self.clock.tick(30)
            while gtk.events_pending():
                gtk.main_iteration()
            # Event phase
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    self.running = False
                elif evt.type == pygame.KEYDOWN:
                    if evt.key == pygame.K_ESCAPE:
                        self.running = False
                    if evt.key == pygame.K_LEFT:
                        self.ship.direction = -1
                    elif evt.key == pygame.K_RIGHT:
                        self.ship.direction = 1
                    elif evt.key == pygame.K_SPACE:
                        self.points = self.points - POINTS_SHOT
                        new_shot = Shot(self)
                        new_shot.rect.midbottom = self.ship.rect.midtop
                        self.shots.add(new_shot)
                elif evt.type == pygame.KEYUP:
                    if evt.key == pygame.K_LEFT and self.ship.direction == -1:
                        self.ship.direction = 0
                    elif evt.key == pygame.K_RIGHT and self.ship.direction == 1:
                        self.ship.direction = 0
            
            # Update phase
            self.ship.update(delta)
            self.shots.update(delta)
            self.enemies.update(delta)
            # Look for shot-enemy collisions
            d = pygame.sprite.groupcollide(self.enemies, self.shots, True, True)
            # add points for each enemy killed
            for ship in d:
                self.points = self.points + POINTS_ENEMY
            # delay between killed all enemies and appears more
            if len(self.enemies) == 0:
                self.count = self.count + 1
            if self.count > 10:
                self.count = 0
                self.level = self.level + 1
                self.level_msg = self._font.render(_('Level: %s') % self.level, 1, (255, 255, 255))
                self.add_enemies(self.level)
            # update score msg
            if not(self.points == self.old_points):
                self.do_score_msg()
            self.old_points = self.points
            # Display phase
            self.screen.fill((0,0,0))
            self.screen.blit(self.points_msg, (self.rect[2] - self._points_large, 10))
            self.screen.blit(self.level_msg, (10, 10))
            for spr in self.enemies:
                self.screen.blit(spr.image, spr.rect, spr.source_rect)
            self.shots.draw(self.screen)
            self.screen.blit(self.ship.image, self.ship.rect)
            pygame.display.flip()
            

class Ship(pygame.sprite.Sprite):
    """The player-controlled ship."""

    def __init__(self, parent):
        super(Ship, self).__init__()
        self.parent = parent
        self.image = parent.ship_img
        self.rect = self.image.get_rect()
        self.direction = 0
        self.speed = 0.1

    def update(self, delta):
        self.rect.move_ip(delta*self.direction*self.speed, 0)
        self.rect.clamp_ip(self.parent.rect)


class Shot(pygame.sprite.Sprite):
    """A single shot fired by the player."""

    def __init__(self, parent):
        super(Shot, self).__init__()
        self.parent = parent
        self.image = parent.shot_img
        self.rect = self.image.get_rect()
        self.speed = 0.2
        
        # Load and play the shot sound
        self.sound = parent.shot_sound
        self.sound.play()

    def update(self, delta):
        self.rect.move_ip(0, -1*delta*self.speed)
        if not self.rect.colliderect(self.parent.rect):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    """An enemy ship."""
    
    def __init__(self, parent):
        super(Enemy, self).__init__()
        self.parent = parent
        self.image = parent.enemy_img
        self.rect = self.image.get_rect()
        self.direction = 1
        self.speed = 0.05
        
        # Setup the animation frames
        self.n_frames = 2
        self.rect.width /= self.n_frames # Make self.rect to be the size of one frame
        self.source_rects = itertools.cycle([self.rect.move(x*self.rect.width, 0) for x in xrange(self.n_frames)])
        self.source_rect = self.source_rects.next() # Load the position of the first frame
        
        # Setup the animation timing
        self.time_per_frame = 200 # ms per frame in the animation
        self.time_left = self.time_per_frame

    def update(self, delta):
        self.time_left -= delta
        if self.time_left <= 0:
            self.time_left += self.time_per_frame
            self.source_rect = self.source_rects.next()
        
        self.rect.move_ip(delta*self.direction*self.speed, 0)
        if self.direction == 1 and self.rect.right >= self.parent.rect.right:
            self.direction *= -1
            self.rect.right = self.parent.rect.right
        elif self.direction == -1 and self.rect.left <= self.parent.rect.left:
            self.direction *= -1
            self.rect.left = self.parent.rect.left

def main():
    s = SpaceWar()
    s.run()

if __name__ == '__main__':
    main()
