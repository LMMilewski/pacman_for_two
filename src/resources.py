""" Basic resource manager

To add new resources to your game put definitions in load_* methods

"""

import os
import pygame
from pygame.locals import *

import color

class Resources:
    """ Collects all resources in one class
    """
    def __init__(self, cfg):
        self.cfg = cfg
        self.sounds     = {}
        self.music     = {}
        self.font      = {}
        self.animation = {}

    def load_all(self):
        if self.cfg.sound:
            self.load_sound_files()
        if self.cfg.music:
            self.load_music_files()
        self.load_animation_files()
        self.load_font_files()

    ## define resources you want to use

    def load_sound_files(self):
        files = ["die",
                 "duke_good",
                 "fruit",
                 "ghost_eat",
                 "intermission",
                 "intro",
                 "powerup",
                 "siren",
                 "waka"]
        for file in files:
            self.load_sound_file(file)

    def load_music_files(self):
        self.load_music_file("one-five-nine")

    def load_animation_files(self):
        self.load_animation_file("level")
        self.load_animation_file("hud")
        self.load_animation_file("dot")
        self.load_animation_file("board")
        self.load_animation_file("powerup")

        self.load_animation_file("pacman-left")
        self.__map_animation_frames("pacman-left", "pacman-down",  self.__rotate_image(90))
        self.__map_animation_frames("pacman-left", "pacman-right", self.__rotate_image(180))
        self.__map_animation_frames("pacman-left", "pacman-up",    self.__rotate_image(270))

        self.__blend_animation_with_color("pacman-left", "pacman-left-yellow", color.by_name["yellow"])
        self.__blend_animation_with_color("pacman-down", "pacman-down-yellow", color.by_name["yellow"])
        self.__blend_animation_with_color("pacman-right", "pacman-right-yellow", color.by_name["yellow"])
        self.__blend_animation_with_color("pacman-up", "pacman-up-yellow", color.by_name["yellow"])

        self.__blend_animation_with_color("pacman-left", "pacman-left-green", color.by_name["green"])
        self.__blend_animation_with_color("pacman-down", "pacman-down-green", color.by_name["green"])
        self.__blend_animation_with_color("pacman-right", "pacman-right-green", color.by_name["green"])
        self.__blend_animation_with_color("pacman-up", "pacman-up-green", color.by_name["green"])

        self.load_animation_file("pacman-stop")
        self.__blend_animation_with_color("pacman-stop", "pacman-stop-yellow", color.by_name["yellow"])
        self.__blend_animation_with_color("pacman-stop", "pacman-stop-green", color.by_name["green"])

        self.load_animation_file("ghost-left")
        self.__map_animation_frames("ghost-left", "ghost-right", self.__flip_image())
        self.load_animation_file("ghost-down")
        self.load_animation_file("ghost-up")

        self.__blend_animation_with_color("ghost-left", "ghost-left-teal", color.by_name["teal"])
        self.__blend_animation_with_color("ghost-right", "ghost-right-teal", color.by_name["teal"])
        self.__blend_animation_with_color("ghost-down", "ghost-down-teal", color.by_name["teal"])
        self.__blend_animation_with_color("ghost-up", "ghost-up-teal", color.by_name["teal"])

        self.__blend_animation_with_color("ghost-left", "ghost-left-pink", color.by_name["pink"])
        self.__blend_animation_with_color("ghost-right", "ghost-right-pink", color.by_name["pink"])
        self.__blend_animation_with_color("ghost-down", "ghost-down-pink", color.by_name["pink"])
        self.__blend_animation_with_color("ghost-up", "ghost-up-pink", color.by_name["pink"])

        self.__blend_animation_with_color("ghost-left", "ghost-left-orange", color.by_name["orange"])
        self.__blend_animation_with_color("ghost-right", "ghost-right-orange", color.by_name["orange"])
        self.__blend_animation_with_color("ghost-down", "ghost-down-orange", color.by_name["orange"])
        self.__blend_animation_with_color("ghost-up", "ghost-up-orange", color.by_name["orange"])

        self.__blend_animation_with_color("ghost-left", "ghost-left-red", color.by_name["red"])
        self.__blend_animation_with_color("ghost-right", "ghost-right-red", color.by_name["red"])
        self.__blend_animation_with_color("ghost-down", "ghost-down-red", color.by_name["red"])
        self.__blend_animation_with_color("ghost-up", "ghost-up-red", color.by_name["red"])

        self.load_animation_file("ghost-frightened")
        self.__blend_animation_with_color("ghost-frightened", "ghost-frightened-blink", color.by_name["white"])
        self.__blend_animation_with_color("ghost-frightened", "ghost-frightened", color.by_name["blue"])

        self.load_animation_file("life")
        self.__blend_animation_with_color("life", "life-yellow", color.by_name["yellow"])
        self.__blend_animation_with_color("life", "life-green", color.by_name["green"])

        self.load_animation_file("eyes-left")
        self.__map_animation_frames("eyes-left", "eyes-right", self.__rotate_image(180))
        self.load_animation_file("eyes-up")
        self.__map_animation_frames("eyes-up", "eyes-down", self.__rotate_image(180))

    def load_font_files(self):
        self.load_font_file("LESSERCO", 14)
        self.load_font_file("LESSERCO", 16)
        self.load_font_file("LESSERCO", 24)
        self.load_font_file("LESSERCO", 96)

    ## use resources

    def sounds_play(self, name, loop=0):
        if self.cfg.sound and name in self.sounds:
            return self.sounds[name].play(loop)

    def music_play(self, name, repeat=-1):
        if self.cfg.music and name in self.music:
            pygame.mixer.music.load(self.music[name])
            pygame.mixer.music.play(repeat)

    def music_stop(self):
        if self.cfg.music:
            pygame.mixer.music.stop()

    def font_render(self, name, size, text, color):
        return self.font[name][size].render(text, 1, color)

    ## load files
    def load_sound_file(self, name):
        sound = self.sounds[name] = pygame.mixer.Sound(self.cfg.sounds_path(name + ".ogg"))
        return sound

    def load_music_file(self, name):
        music = self.music[name] = self.cfg.music_path(name + ".ogg")
        return music

    def load_font_file(self, name, size):
        try:
            self.font[name]
        except:
            self.font[name] = {}
        font = self.font[name][size] = pygame.font.Font(self.cfg.font_path(name + ".ttf"), size)
        return font

    def load_animation_file(self, name):
        if os.path.isfile(self.cfg.gfx_path(name) + ".png"): # there is only one static image
            img = self.__load_image(self.cfg.gfx_path(name) + ".png")
            self.animation[name] = []
            self.animation[name].append(img)
            return self.animation
        else: # there is a sequence of images - an animation
            count = 0
            animation = []
            while True:
                fname = self.cfg.gfx_path(name) + "-" + str(count) + ".png"
                if not os.path.isfile(fname):
                    break
                animation.append(self.__load_image(fname))
                count += 1
            self.animation[name] = animation
            return animation

    def __load_image(self, fname):
        return pygame.image.load(self.cfg.gfx_path(fname)).convert_alpha()

    def __blend_animation_with_color(self, name, new_name, color):
        """ Usefull for theme/skin creation

        You create file with everything in mostly white color, then
        you use this function and you get new animation with changed
        colors to 'color'
        """
        animation = self.animation[name]
        new_animation = []
        for frame in animation:
            new_frame = frame.copy()
            s = pygame.Surface(frame.get_size()).convert_alpha()
            s.fill(color)
            new_frame.blit(s, (0,0), None, BLEND_RGBA_MULT)
            new_animation.append(new_frame)
        self.animation[new_name] = new_animation
        return new_animation

    def __map_animation_frames(self, name, new_name, f):
        """ Apply f to all frames of an animation and store as new animation
        """
        animation = self.animation[name]
        new_animation = []
        for frame in animation:
            new_frame = f(frame)
            new_animation.append(new_frame)
        self.animation[new_name] = new_animation
        return new_animation

    def __rotate_image(self, degrees):
        return lambda image: pygame.transform.rotate(image, degrees)

    def __flip_image(self):
        return lambda image: pygame.transform.flip(image, True, False)
