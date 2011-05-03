from const import *

def direction_to_vector(direction):
    if direction == DIR_LEFT:
        return (-1,0)
    if direction == DIR_DOWN:
        return (0,1)
    if direction == DIR_RIGHT:
        return (1,0)
    if direction == DIR_UP:
        return (0,-1)
    if direction == DIR_STOP:
        return (0,0)
