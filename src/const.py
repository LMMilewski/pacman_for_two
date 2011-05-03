DIR_LEFT                      = 0
DIR_DOWN                      = 1
DIR_RIGHT                     = 2
DIR_UP                        = 3
DIR_STOP                      = 4

ORIGIN_TOP_LEFT               = 4
ORIGIN_CENTER                 = 5

RED_GHOST_ID                  = 0
TEAL_GHOST_ID                 = 1
PINK_GHOST_ID                 = 2
ORANGE_GHOST_ID               = 3

GHOST_STATE_STOPPED           = 6
GHOST_STATE_IMPRISONED        = 7
GHOST_STATE_LEAVING_PRISON    = 8
GHOST_STATE_CHASE             = 9
GHOST_STATE_SCATTER           = 10

GAME_PHASE_NONE               = 12
GAME_PHASE_CHASE              = 13
GAME_PHASE_SCATTER            = 14

GHOST_SPRITE_LEFT             = DIR_LEFT
GHOST_SPRITE_DOWN             = DIR_DOWN
GHOST_SPRITE_RIGHT            = DIR_RIGHT
GHOST_SPRITE_UP               = DIR_UP
GHOST_SPRITE_FRIGHTENED       = DIR_UP + 1
GHOST_SPRITE_FRIGHTENED_BLINK = DIR_UP + 2
GHOST_SPRITE_EYES             = DIR_UP + 3
GHOST_SPRITE_EYES_LEFT        = GHOST_SPRITE_EYES + DIR_LEFT
GHOST_SPRITE_EYES_DOWN        = GHOST_SPRITE_EYES + DIR_DOWN
GHOST_SPRITE_EYES_RIGHT       = GHOST_SPRITE_EYES + DIR_RIGHT
GHOST_SPRITE_EYES_UP          = GHOST_SPRITE_EYES + DIR_UP
