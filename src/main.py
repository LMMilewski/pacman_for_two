import sys
import pygame
from pygame.locals import *

import color
from config import Config
from game_fsm import GameState, GameFsm
from sprite import Sprite
from resources import Resources
from const import *
from utils import *
from random import *

def cells_euclidean_2d_distance_squared(grid_cell_size, cell0, cell1):
    pos0 = cell_to_position(grid_cell_size, cell0)
    pos1 = cell_to_position(grid_cell_size, cell1)
    return euclidean_2d_distance_squared(pos0, pos1)

def euclidean_2d_distance_squared(pos0, pos1):
    x0,y0 = pos0
    x1,y1 = pos1
    dx = x1 - x0
    dy = y1 - y0
    return dx*dx+dy*dy

def position_to_cell(grid_cell_size, position):
    px, py = position[0] - 2, position[1] - 2
    cw, ch = grid_cell_size
    cx, cy = int(px / cw) + 11, int(py / ch) + 11
    return (cx, cy)

def cell_to_position(grid_cell_size, cell):
    cx, cy = cell
    cx -= 11
    cy -= 11
    cw, ch = grid_cell_size
    return (cx * cw + 2, cy * ch + 2)

def current_cell(movable):
    return position_to_cell(movable.cfg.grid_cell_size, movable.position)

def cell_center(grid_cell_size, cell):
    cx,cy = cell_to_position(grid_cell_size, cell)
    cx += grid_cell_size[0] / 2
    cy += grid_cell_size[1] / 2
    return (cx, cy)

class SoundRepeated:
    """ Allows creating a sound that is being constantly being played
    in a loop if you keep calling play method. If you don't call play
    mehod for 'cooldown' seconds then the sound is stopped

    Remember to call update in main loop
    """
    def __init__(self, name, res, cooldown = None):
        """
        res Resource manager
        name Name of the sound being played
        cooldown If play is not called in 'cooldown' seconds the sound is stopped

        if you set cooldown = None then you have to explicitly stop the
        sound by calling stop method
        """
        self.res = res
        self.name = name
        self.cooldown = cooldown
        self.timer = 0
        self.channel = None

    def play(self):
        if self.timer == 0:
            self.channel = self.res.sounds_play(self.name, -1)
        self.timer = self.cooldown

    def stop(self):
        if self.channel == None:
            return
        self.timer = 0
        self.channel.stop()
        self.channel = None

    def update(self, dt):
        if self.timer == None:
            return
        if self.timer != 0:
            self.timer -= dt
        if self.timer < 0:
            self.stop()

class Ghost:
    def __init__(self, cfg, position, direction, color, res, pacmans, ghosts, random, game):
        self.cfg = cfg
        self.position = position
        self.direction = direction
        self.next_direction = self.direction
        self.color = color
        self.res = res
        self.pacmans = pacmans
        self.ghosts = ghosts
        self.state = GHOST_STATE_STOPPED
        self.frightened = False
        self.random = random
        self.game = game
        self.isdead = False # if the ghost is dead he is show as eyes,
                            # he is not colliding with anything and he
                            # returns straight to home

        self.target = pacmans[0].position
        self.sprite = [ Sprite("ghost-left-"+color, self.res, 0.1),
                        Sprite("ghost-down-"+color, self.res, 0.1),
                        Sprite("ghost-right-"+color, self.res, 0.1),
                        Sprite("ghost-up-"+color, self.res, 0.1),
                        Sprite("ghost-frightened", self.res, 0.5),
                        Sprite("ghost-frightened-blink", self.res, 0.5),
                        Sprite("eyes-left", self.res),
                        Sprite("eyes-down", self.res),
                        Sprite("eyes-right", self.res),
                        Sprite("eyes-up", self.res), ]

        self.prev_cell = position_to_cell(self.cfg.grid_cell_size, self.position)
        self.curr_cell = self.prev_cell

    def set_board(self, board):
        self.board = board

    def start(self):
        if self.state == GHOST_STATE_STOPPED:
            self.state = GHOST_STATE_IMPRISONED

    def frighten(self):
        if not self.isdead:
            self.__reverse_direction()
            self.frightened = True

    def unfrighten(self):
        self.frightened = False

    def update(self, dt):
        # to understand how ghost logic works please visit
        # http://home.comcast.net/~jpittman2/pacman/pacmandossier.html#Chapter_4

        if self.state == GHOST_STATE_STOPPED:
            return
        elif self.state == GHOST_STATE_IMPRISONED: # go up/down vainly
            self.__update_imprisoned(dt)
        elif self.state == GHOST_STATE_LEAVING_PRISON: # go through prison door and chase
            self.__update_leave_prison(dt)
        elif self.state in (GHOST_STATE_CHASE, GHOST_STATE_SCATTER):
            self.__update_playing(dt)

        # compute new position
        px, py = self.position
        dx, dy = direction_to_vector(self.direction)
        speed = self.cfg.ghost_eyes_speed if self.isdead else self.cfg.ghost_speed
        npx, npy = px + dx * dt * speed, py + dy * dt * speed

        # tunnel
        if npx > 248:
            npx = -4
        if npx < -4:
            npx = 248

        # update the position and current sprite
        self.position = npx, npy
        self.sprite[self.__current_sprite_id()].update(dt)

    def __current_sprite_id(self):
        if self.isdead:
            return GHOST_SPRITE_EYES + self.direction
        elif self.frightened:
            if abs(self.game.frightened_timer - 1.0) < 0.1: # blink when frighten mode is about to finish
                return GHOST_SPRITE_FRIGHTENED_BLINK
            elif abs(self.game.frightened_timer - 0.50) < 0.1: # blink when frighten mode is about to finish
                return GHOST_SPRITE_FRIGHTENED_BLINK
            else:
                return GHOST_SPRITE_FRIGHTENED
        else:
            return self.direction

    def __update_imprisoned(self, dt):
        """ While imprisoned ghosts wander up and down doing nothing
        """
        if self.color == 'red':
            self.state = GHOST_STATE_CHASE
        x, y = self.position
        if self.direction == DIR_UP and y <= 108:
            self.direction = DIR_DOWN
        elif self.direction == DIR_DOWN and y > 113:
            self.direction = DIR_UP

    def __update_leave_prison(self, dt):
        """ Make ghost leave the prison. First it guides him to the
        center of the prison and then up. The state is changed to
        CHASE when the ghost leaves the prison
        """
        if self.color == 'orange':      # orange should go left first (he is on the right side)
            self.direction = DIR_LEFT
        if self.color == 'teal':        # teal should choose right as he is on the left
            self.direction = DIR_RIGHT

        x, y = self.position            # if ghost reached center - make him go up
        if x < 120 and x > 118:
            self.direction = DIR_UP
            self.target = (27,22)

        if y < 90:                      # if ghost reached entrance - go to chase state
            self.direction = DIR_LEFT
            self.state = GHOST_STATE_CHASE

        self.__pursue_target(dt)

    def __update_playing(self, dt):
        """ When the ghost leaves the prison he is 'playing'. He can
        be in scatter mode, he can chase the player or he can be
        frightened

        Basically all ghosts pursue a target cell. When ghost reaches
        a cell he decides what he will do when he reaches next cell in
        his current direction. He can't change that decision later. He
        never can reverse his direction in chase state.

        When he makes a decision, ghost always chooses to go to the
        cell nearest to his target cell.

        Target cell depends on ghost color and current state of the
        ghost
        """
        if self.isdead and self.curr_cell == (27,22):
            self.isdead = False

        # center of current cell
        self.curr_cell = current_cell(self)
        cx, cy = cell_center(self.cfg.grid_cell_size, self.curr_cell)

        # ghost must pass cell center if he wants to turn (so he is
        # always at the center of cell)
        if self.direction == DIR_LEFT and self.position[0] > cx:
            return
        if self.direction == DIR_RIGHT and self.position[0] < cx:
            return;
        if self.direction == DIR_UP and self.position[1] > cy:
            return
        if self.direction == DIR_DOWN and self.position[1] < cy:
            return

        # try to set new direction
        if self.curr_cell != self.prev_cell:
            self.prev_cell = self.curr_cell
            self.direction = self.next_direction
            self.position = cx,cy # align ghost to the center of the cell
            # choose next target cell
            if self.isdead:
                self.target = (27,22)
            elif self.frightened:
                self.target = self.__frightened_target()
            else:
                if self.color == 'red':
                    self.target = self.__red_target()
                elif self.color == 'pink':
                    self.target = self.__pink_target()
                elif self.color == 'teal':
                    self.target = self.__teal_target()
                elif self.color == 'orange':
                    self.target = self.__orange_target()
            self.__pursue_target(dt)

    def __pursue_target(self, dt):
        # compute next cell in current direction
        cell = self.__get_cell_in_direction(current_cell(self), self.direction)
        # check all possible directions from cx,cy - choose the
        # one that is closest to the target (according to
        # euclidean norm)
        distance = cells_euclidean_2d_distance_squared
        best_cell_distance = 999999 # infinity
        for direction in [DIR_UP, DIR_LEFT, DIR_DOWN, DIR_RIGHT]:
            direction_cxy = self.__get_cell_in_direction(cell, direction)
            # can't reverse direction
            if (4 + direction - self.direction) % 4 == 2:
                continue
            # position in the direction must be valid
            if self.board.get_at(direction_cxy)[1] != 255:
                continue
            # position in the direction must be closest to target
            d = distance(self.cfg.grid_cell_size, direction_cxy, self.target)
            if d < best_cell_distance:
                best_cell_distance = d
                self.next_direction = direction

    def __get_cell_in_direction(self, (cell_x, cell_y), direction):
        dx, dy = direction_to_vector(direction)
        return (cell_x + dx, cell_y + dy)

    def scatter(self):
        """Switch ghost to scatter state"""
        if self.state == GHOST_STATE_CHASE:
            self.__reverse_direction();
        self.state = GHOST_STATE_SCATTER

    def chase(self):
        """Switch ghost to chase state"""
        if self.state == GHOST_STATE_SCATTER:
            self.__reverse_direction();
        self.state = GHOST_STATE_CHASE

    def __reverse_direction(self):
        self.next_direction = (self.direction + 2) % 4

    def __frightened_target(self):
        """Random direction

        get random direction and try directions counter clockwise
        unless you finde valid one. Still you can neighter enter
        nonempty cell nor you can reverse direction """
        directions_to_try = range(self.random.integer(DIR_LEFT, DIR_UP), DIR_STOP)
        directions_to_try.extend([DIR_LEFT, DIR_DOWN, DIR_RIGHT, DIR_UP]) # all directions must be on list
        cell = self.__get_cell_in_direction(current_cell(self), self.direction)
        for direction in directions_to_try:
            direction_cxy = self.__get_cell_in_direction(cell, direction)
            # can't reverse direction
            if (4 + direction - self.direction) % 4 == 2:
                continue
            # position in the direction must be valid
            if self.board.get_at(direction_cxy)[1] != 255:
                continue
            return direction_cxy # get first that matches requirements
        return self.target # in case that all directions are invalid

    def __red_target(self):
        """ Closest pacman's cell
        """
        if self.state == GHOST_STATE_SCATTER:
            return (41,9)
        else:
            closest_pacman = self.__get_closest_pacman()
            return position_to_cell(self.cfg.grid_cell_size, closest_pacman.position)

    def __pink_target(self):
        """ Four cells in front of pacman
        """
        if self.state == GHOST_STATE_SCATTER:
            return (13,9)
        else:
            closest_pacman = self.__get_closest_pacman()
            cx, cy = position_to_cell(self.cfg.grid_cell_size, closest_pacman.position)
            dx, dy = direction_to_vector(closest_pacman.direction)
            return (cx + dx*4, cy + dy*4)

    def __teal_target(self):
        """ Get cell P two cells in front of Pacman. Get cell R -
        current red ghosts cell. Find vector v = P - R. Target is a
        cell = P + v
        """
        if self.state == GHOST_STATE_SCATTER:
            return (42,42)
        else:
            closest_pacman = self.__get_closest_pacman()
            px, py = position_to_cell(self.cfg.grid_cell_size, closest_pacman.position)
            rx, ry = position_to_cell(self.cfg.grid_cell_size, self.ghosts[RED_GHOST_ID].position) # red ghost
            dx, dy = px - rx, py - ry
            tx, ty = px + dx, py + dy
            return (tx, ty)

    def __orange_target(self):
        """ If the distance (euclidean) to closest pacman is greater
        or equal than 8 then attack him directly (just as red ghost
        would do). If the distance is less than 8 - go to your scatter
        point (bottom left corner)
        """
        if self.state == GHOST_STATE_SCATTER:
            return (12,42)
        else:
            cell = position_to_cell(self.cfg.grid_cell_size, self.position)
            closest_pacman = self.__get_closest_pacman()
            pacman_cell = position_to_cell(self.cfg.grid_cell_size, closest_pacman.position)
            # we don't use cell_* function here because we want the distance in cells not in pixels
            if euclidean_2d_distance_squared(pacman_cell, cell) >= 64: # sqrt(x) < 8
                return pacman_cell
            else:
                return (12,42)

    def __get_closest_pacman(self):
        closest_pacman = self.pacmans[0]
        closest_distance = euclidean_2d_distance_squared(self.position, closest_pacman.position)
        for pacman in self.pacmans:
            if not pacman.is_alive():
                continue
            distance = euclidean_2d_distance_squared(self.position, pacman.position)
            if distance < closest_distance:
                closest_distance = distance
                closest_pacman = pacman
        return closest_pacman

    def display(self, screen):
        self.sprite[self.__current_sprite_id()].display(screen, self.position)
        px, py = cell_to_position(self.cfg.grid_cell_size, self.target)

        if self.cfg.display_position:
            pygame.draw.rect(screen, color.by_name[self.color], (px-1, py-1, 10,10))

class Pacman:
    def __init__(self, cfg, direction, color, res):
        self.cfg = cfg
        self.direction = direction
        self.color = color
        self.res = res
        self.points = 0
        self.lives = 3

        self.sprite = [ Sprite("pacman-left-"+color,  self.res, 0.03),
                        Sprite("pacman-down-"+color,  self.res, 0.03),
                        Sprite("pacman-right-"+color, self.res, 0.03),
                        Sprite("pacman-up-"+color,    self.res, 0.03),
                        Sprite("pacman-stop-"+color,  self.res, 0.03) ]

        self.reset()
        self.speed = self.cfg.packman_standard_speed

    def set_board(self, board):
        self.board = board

    def reset(self):
        """ Reset pacman state when the level is changed or pacman is killed
        """
        self.position = self.cfg.pacman_position[self.color]
        self.direction = DIR_STOP
        for sprite in self.sprite:
            sprite.reset_animation()

    def is_alive(self):
        return self.lives > 0

    def update(self, dt):
        # check if you can change the direction
        self.direction = self.next_direction

        # compute new position
        px, py = self.position
        dx, dy = direction_to_vector(self.direction)
        npx, npy = px + dx * dt * self.speed, py + dy * dt * self.speed

        # cornering (if pacman is turning near the edge of the cell,
        # his position is adjusted so that he is at the center of the
        # cell
        desired_pos = cell_center(self.cfg.grid_cell_size, current_cell(self))
        if self.direction in [DIR_UP, DIR_DOWN]:
            if npx < desired_pos[0]:
                npx += 1
            if npx > desired_pos[0]:
                npx -= 1
        if self.direction in [DIR_LEFT, DIR_RIGHT]:
            if npy < desired_pos[1]:
                npy += 1
            if npy > desired_pos[1]:
                npy -= 1

        # tunnel
        if npx > 248:
            npx = -4
        if npx < -4:
            npx = 248

        # update position if you can enter new cell
        cx, cy = position_to_cell(self.cfg.grid_cell_size, (npx, npy))
        if self.board.get_at((cx, cy))[1] == 255: # if the field is green
            self.position = npx, npy

        # update animation
        self.sprite[self.direction].update(dt)

    def display(self, screen):
        self.sprite[self.direction].display(screen, self.position)

class PacmanGame(GameState):
    def __init__(self, cfg, res):
        """ Initializes the game

        takes care of configuration, resrouce and sprite initialization
        """
        self.cfg = cfg
        self.res = res
        self.players_count = 1
        self.life_sprite = {
            "yellow" : Sprite("life-yellow", self.res),
            "green"  : Sprite("life-green", self.res)
            }
        self.dot     = Sprite("dot", self.res)
        self.level   = Sprite("level", self.res, None, ORIGIN_TOP_LEFT)
        self.powerup = Sprite("powerup", self.res, 0.5)
        self.hud     = Sprite("hud", self.res, None, ORIGIN_TOP_LEFT)

        self.sound_siren = SoundRepeated("siren", self.res)
        self.sound_waka = SoundRepeated("waka", self.res, 0.5)

    def init(self, screen):
        """ Initialized the state of the game

        This is run only once - when the game fsm is started. Takes
        care of initial state of the game, starts first level
        """
        self.__set_pacmans()
        self.set_level(1)

    def kill_pacman(self, pacman):
        """ Called when a pacman die.

        Move ghosts to their initial positions and resets their state.
        """
        pacman.lives -= 1
        self.res.sounds_play("die")
        self.__reset_level_state()

    def set_level(self, level_num):
        """ Called when the level is changed

        it clears the board, the ghosts and game states (frightened,
        chase/scatter, etc.)
        """
        if level_num == 1:
            self.res.sounds_play("intro")
        else:
            self.res.sounds_play("intermission")

        self.board = self.res.animation["board"][0].copy()
        self.phase_num = 0
        self.level_num = level_num
        self.__reset_level_state()
        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            pacman.set_board(self.board)
        self.dots_left = self.cfg.dots_to_eat

    def go_to_next_level(self):
        self.set_level(self.level_num+1)

    def __reset_level_state(self):
        self.phase = GAME_PHASE_NONE
        self.phase_timer = 0
        self.frighten_mode = False
        self.frightened_timer = 0
        self.game_started = False
        self.random = Random(13)
        self.__set_ghosts()
        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            pacman.reset()
        self.sound_siren.stop()
        self.sound_waka.stop()

    def __set_pacmans(self):
        self.pacman = []
        self.pacman.append(Pacman(self.cfg, DIR_STOP, "yellow", self.res))

    def __set_ghosts(self):
        self.ghost = []
        self.ghost.append(Ghost(self.cfg, self.cfg.ghost_red_position, DIR_LEFT, "red", self.res, self.pacman, self.ghost, self.random, self))
        self.ghost.append(Ghost(self.cfg, self.cfg.ghost_teal_position, DIR_UP, "teal", self.res, self.pacman, self.ghost, self.random, self))
        self.ghost.append(Ghost(self.cfg, self.cfg.ghost_pink_position, DIR_UP, "pink", self.res, self.pacman, self.ghost, self.random, self))
        self.ghost.append(Ghost(self.cfg, self.cfg.ghost_orange_position, DIR_UP, "orange", self.res, self.pacman, self.ghost, self.random, self))
        for ghost in self.ghost:
            ghost.set_board(self.board)

    def __change_phase(self):
        """Change phase scatter->chase, chase->scatter, none->scatter
        """
        if self.phase == GAME_PHASE_NONE:
            self.phase = GAME_PHASE_SCATTER
        elif self.phase == GAME_PHASE_CHASE:
            self.phase = GAME_PHASE_SCATTER
        elif self.phase == GAME_PHASE_SCATTER:
            self.phase = GAME_PHASE_CHASE
        self.phase_num += 1
        self.phase_timer = self.cfg.get_phase_duration(self.level_num, self.phase_num)

        if self.phase_timer == 0: # this makes ghost reverse direction when timer is 0
            return

        for ghost in self.ghost:
            if self.phase == GAME_PHASE_CHASE:
                ghost.chase()
            elif self.phase == GAME_PHASE_SCATTER:
                ghost.scatter()

    def add_green_pacman(self):
        if len(self.pacman) < 2:
            self.pacman.append(Pacman(self.cfg, DIR_STOP, "green", self.res))
            self.pacman[1].reset()
            self.pacman[1].set_board(self.board)

    def update(self, dt):
        if not self.game_started:
            return

        self.sound_siren.play()
        self.sound_siren.update(dt)
        self.sound_waka.update(dt)

        if self.frighten_mode:
            self.frightened_timer -= dt
            if self.frightened_timer < 0:
                self.unfrighten_ghosts()
        else:
            self.phase_timer -= dt
            if self.phase_timer < 0:
                self.__change_phase()

        self.powerup.update(dt)

        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            pacman.update(dt)

        for ghost in self.ghost:
            ghost.update(dt)

        # check collision with dots
        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            cx, cy = position_to_cell(self.cfg.grid_cell_size, pacman.position)
            r,g,b,a = self.board.get_at((cx,cy))
            if r == 255 and b == 255: # energizer
                self.res.sounds_play("powerup")
                pacman.points += 50
                self.board.set_at((cx,cy),(0,255,0,1))
                self.frighten_ghosts()
            elif r == 255: # small dot
                self.sound_waka.play()
                pacman.points += 10
                self.board.set_at((cx,cy),(0,255,0,1))
                self.dots_left -= 1
                if self.dots_left <= 0:
                    self.go_to_next_level()
                    return

        # check collision with ghosts
        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            for ghost in self.ghost:
                if not ghost.isdead and current_cell(pacman) == current_cell(ghost):
                    if self.frighten_mode: # ghost is eaten by the pacman
                        pacman.points += 1000
                        ghost.isdead = True
                        self.res.sounds_play("ghost_eat")
                    else: # pacman is killed by the ghost
                        self.kill_pacman(pacman)

    def display(self, screen):
        self.level.display(screen, (0,0))
        bw, bh = self.cfg.board_size

        gw,gh = self.cfg.grid_size
        for cy in range(0,gh):
            for cx in range(0,gw):
                r,g,b,a = self.board.get_at((cx,cy))
                px, py = cell_to_position(self.cfg.grid_cell_size, (cx, cy))
                if b == 255: # power-up
                    self.powerup.display(screen, (px + 4, py + 4))
                elif r == 255: # dot
                    self.dot.display(screen, (px + 4, py + 4))

        for ghost in self.ghost:
            ghost.display(screen)

        if self.cfg.display_grid:
            gw,gh = self.cfg.grid_size
            for cy in range(0,gh):
                for cx in range(0,gw):
                    px, py = cell_to_position(self.cfg.grid_cell_size, (cx, cy))
                    pygame.draw.line(screen, (255,0,0), (0,py), (self.cfg.resolution[0], py))
                    pygame.draw.line(screen, (255,0,0), (px,0), (px,self.cfg.resolution[1]))

        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            pacman.display(screen)

        self.hud.display(screen, (bw,0))

        if not self.game_started:
            text_ready = self.res.font_render("LESSERCO", 16, "READY!", (255,255,0))
            screen.blit(text_ready, (100,125))

        text_level = self.res.font_render("LESSERCO", 24, "LEVEL:", (255,0,0))
        text_level_num = self.res.font_render("LESSERCO", 24, str(self.level_num), (255,255,0))
        screen.blit(text_level, (bw+10, 10))
        screen.blit(text_level_num, (bw+10, 30))

        text_points = self.res.font_render("LESSERCO", 24, "POINTS:", (255,0,0))
        screen.blit(text_points, (bw+10, 50))
        pos_y = 70
        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            text_points = self.res.font_render("LESSERCO", 24, str(pacman.points), color.by_name[pacman.color])
            screen.blit(text_points, (bw+10, pos_y))
            pos_y += 20

        text_lives = self.res.font_render("LESSERCO", 24, "LIVES:", color.by_name["red"])
        screen.blit(text_lives, (bw+10, pos_y))
        pos_y += 10+20
        for pacman in self.pacman:
            if not pacman.is_alive():
                continue
            pos_x = bw+10
            for life in range(pacman.lives):
                self.life_sprite[pacman.color].display(screen, (pos_x, pos_y))
                pos_x += 12
            pos_y += 20

        if self.frighten_mode:
            text_frighten_mode = self.res.font_render("LESSERCO", 24, "FRIGHTEN", (255,0,0))
            text_frighten_timer = self.res.font_render("LESSERCO", 24, str(self.frightened_timer), (255,0,0))
            screen.blit(text_frighten_mode, (bw+10, 140))
            screen.blit(text_frighten_timer, (bw+10, 160))

        text_phase = self.res.font_render("LESSERCO", 24, "Phase:", (255,0,0))
        phase_name = ""
        if self.phase == GAME_PHASE_SCATTER:
            phase_name = "scatter"
        elif self.phase == GAME_PHASE_CHASE:
            phase_name = "chase"
        text_phase_name = self.res.font_render("LESSERCO", 24, phase_name, (255,0,0))
        text_phase_timer = self.res.font_render("LESSERCO", 24, str(self.phase_timer), (255,0,0))
        screen.blit(text_phase, (bw+10,180))
        screen.blit(text_phase_name, (bw+10, 200))
        screen.blit(text_phase_timer, (bw+10, 220))

        if self.cfg.display_position:
            for ghost in self.ghost:
                text = self.res.font_render("LESSERCO", 14, str(ghost.curr_cell), color.by_name[ghost.color])
                screen.blit(text, ghost.position)
                cx,cy = cell_to_position(self.cfg.grid_cell_size, ghost.curr_cell)
                pygame.draw.rect(screen, (0,0,255), (cx,cy,8,8),1)
                px,py = ghost.position
                pygame.draw.rect(screen, (0,255,0), (px, py, 1, 1), 1)

                for pacman in self.pacman:
                    cell = position_to_cell(self.cfg.grid_cell_size, pacman.position)
                    text = self.res.font_render("LESSERCO", 14, str(cell), color.by_name[pacman.color])
                    cx,cy = cell_to_position(self.cfg.grid_cell_size, cell)
                    px,py = pacman.position
                    screen.blit(text, pacman.position)
                    pygame.draw.rect(screen, (0,0,255), (cx,cy,8,8),1)
                    pygame.draw.rect(screen, (0,255,0), (px, py, 1, 1), 1)

    def frighten_ghosts(self):
        self.frighten_mode = True
        self.frightened_timer = 4
        for ghost in self.ghost:
            ghost.frighten()

    def unfrighten_ghosts(self):
        self.frighten_mode = False
        self.frightened_timer = 0
        for ghost in self.ghost:
            ghost.unfrighten()

    def __start_game(self):
        if not self.game_started:
            self.game_started = True
            for ghost in self.ghost:
                ghost.start()

    def process_event(self, event):
        if event.type == QUIT:
            sys.exit()
        if event.type == KEYDOWN:
            if event.key != K_0:
                self.__start_game()
            if event.key == K_ESCAPE:
                sys.exit()
            elif event.key == K_LEFT:
                self.pacman[0].next_direction = DIR_LEFT
            elif event.key == K_RIGHT:
                self.pacman[0].next_direction = DIR_RIGHT
            elif event.key == K_UP:
                self.pacman[0].next_direction = DIR_UP
            elif event.key == K_DOWN:
                self.pacman[0].next_direction = DIR_DOWN
            elif event.key == K_a:
                self.pacman[1].next_direction = DIR_LEFT
            elif event.key == K_d:
                self.pacman[1].next_direction = DIR_RIGHT
            elif event.key == K_w:
                self.pacman[1].next_direction = DIR_UP
            elif event.key == K_s:
                self.pacman[1].next_direction = DIR_DOWN
            elif event.key == K_1:
                for ghost in self.ghost:
                    if not ghost.isdead:
                        ghost.isdead = True
                        break;
            elif event.key == K_2:
                self.cfg.display_position = not self.cfg.display_position
            elif event.key == K_3:
                self.cfg.display_grid = not self.cfg.display_grid
            elif event.key == K_4:
                for ghost in self.ghost:
                    if ghost.state == GHOST_STATE_CHASE:
                        ghost.scatter()
                    elif ghost.state == GHOST_STATE_SCATTER:
                        ghost.chase()
            elif event.key == K_5:
                if self.frighten_mode:
                    self.unfrighten_ghosts()
                else:
                    self.frighten_ghosts()
            elif event.key == K_9:
                self.go_to_next_level()
            elif event.key == K_0:
                self.add_green_pacman()

def main():
    cfg = Config()
    fsm = GameFsm(cfg)
    res = Resources(cfg)
    res.load_all()
    fsm.set_state(PacmanGame(cfg, res))
    pygame.display.set_caption("Pacman4two")
    pygame.mouse.set_visible(not cfg.fullscreen)
    fsm.run()
