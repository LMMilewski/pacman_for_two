""" Sprite is a synonym to animated object here

Sprites remember everything that is needed to draw them (i.e. frame
num, last frame change, image name)
"""

from const import *

class Sprite:
    def __init__(self, name, res, delay = None, draw_origin = ORIGIN_CENTER):
        self.name = name
        self.res = res
        self.delay = delay
        self.draw_origin = draw_origin
        self.frames_count = len(self.res.animation[name])
        self.reset_animation()

    def reset_animation(self):
        self.current_frame_index = 0
        self.next_frame_change_time = self.delay

    def update(self, dt):
        if self.delay == None:
            return
        self.next_frame_change_time -= dt
        if (self.next_frame_change_time < 0):
            self.next_frame_change_time += self.delay
            self.current_frame_index += 1
            self.current_frame_index %= self.frames_count

    def current_frame(self):
        return self.res.animation[self.name][self.current_frame_index]

    def display(self, screen, position):
        img = self.current_frame()
        if self.draw_origin == ORIGIN_TOP_LEFT:
            screen.blit(img, position)
        elif self.draw_origin == ORIGIN_CENTER:
            w,h = img.get_size()
            x,y = position
            display_position = (x-w/2, y-h/2)
            screen.blit(img, display_position)
