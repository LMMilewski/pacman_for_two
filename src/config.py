""" Proviedes global game informations

Store there all configuration variables instead of hardcoding them in
the game code.

It provides public access to its fields, so:
  - you should mostly read these variables
  - modify them only if you have to. Do it in organized way or your
    game will work unexpectedly
"""
import os, sys

class Config:
    def __init__(self):
        ## general stuff
        self.sound = not "--nosounds" in sys.argv
        self.music = not "--nomusic" in sys.argv
        self.resolution = 320,240 # in this resolution the game is blited onto Surface
        self.screen_resolution = 800,600 # just before swap buffers the screen is scaled to this resolution
        self.board_size = 240,240
        self.fullscreen = "--fullscreen" in sys.argv
        self.fps_limit = 60
        self.grid_cell_size = 7.05, 7.58
        self.grid_size = 54, 52
        self.display_grid = False
        self.display_target_cells = False
        self.display_position = False
        self.dots_to_eat = 264 # 260 normal + 4 powerups

        self.pacman_position = {
            "yellow" : (125, 180),
            "green"  : (112, 180)
            }
        self.packman_standard_speed = 50

        self.ghost_red_position = 120,90
        self.ghost_orange_position = 135,110
        self.ghost_teal_position = 105,110
        self.ghost_pink_position = 120,110
        self.ghost_speed = 40
        self.ghost_eyes_speed = 200

        ## paths
        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.__path={}
        for data_type in ("gfx", "sounds", "music", "font"):
            self.__path[data_type] = os.path.join(base_path, data_type)
        # you can't inline __add_path_getter method because in python
        # closures are create by function calls
        for k, v in self.__path.items():
            self.__add_path_getter(k,v)

    def __add_path_getter(self, k, v):
            setattr(Config,
                    k + "_path",
                    lambda self_, fname: os.path.join(v, fname))

    def get_phase_duration(self, level, phase_num):
        """Returns duration of scatter/chase phase in seconds
        """
        if phase_num >= 8:
            return 9999999
        lvl_1    = [0,7,20,7,20,5,20,  5]
        lvl_2_4  = [0,7,20,7,20,5,1033,0] # 0 is simple reversal of direction
        lvl_gt_5 = [0,5,20,5,20,5,1037,0]
        if level == 1:
            return lvl_1[phase_num]
        elif level >= 2 and level <= 4:
            return lvl_2_4[phase_num]
        else:
            return lvl_gt_5[phase_num]
