#!/usr/bin/env python

import pygame, sys
from pygame.locals import *
import random
import math

class Setup:
    PaddleLimit = (0, 1024)
    BoardSize = (320, 240)
    BrickStartupPattern = ([1]*4 + [0]*2)*3 + [0]*(4+2)*2
    BrickGroupSizes = [6, 6, 6, 6, 6]
    BricksPerLine = 16

    BrickSize = (18, 5)
    BrickBorder = (1, 1)
    BallSize = (4, 4)
    PaddleSize = (30, 4)
    PaddleTop = 222
    BoardMargin = (0, 0)

    DisplaySize = (800, 600)

# 10 bricks per line: width 30, border 1, margin 0
# 16 bricks per line: width 18, border 1, margin 0
# 20 bricks per line: width 14, border 1, margin 0
# 4 lines per group: height 5, border 1, margin 0, paddletop 222
# 5 lines per group: height 4, border 1, margin 0, paddletop 222

class Color:
    black = (0, 0, 0)
    white = (255, 255, 255)
    blue = (0, 0, 170)
    red = (153, 0, 0)
    green = (0, 204, 0)
    yellow = (255, 235, 0)


def vector_from_angle(rad_angle, length):
    return (length * math.cos(rad_angle), -length * math.sin(rad_angle))

def get_paddle_rect(logical_pos):
    normalized = float(logical_pos - Setup.PaddleLimit[0]) / (Setup.PaddleLimit[1] - Setup.PaddleLimit[0])
    max_left = Setup.BoardSize[0] - Setup.PaddleSize[0] - 1
    left = min(max_left, int(max_left * normalized))
    return (left, Setup.PaddleTop) + Setup.PaddleSize

def get_brick_rect(row, col):
    t = (Setup.BrickSize[0] + 2 * Setup.BrickBorder[0], \
         Setup.BrickSize[1] + 2 * Setup.BrickBorder[1])
    return (Setup.BoardMargin[0] + col * t[0] + Setup.BrickBorder[0], \
            Setup.BoardMargin[1] + row * t[1] + Setup.BrickBorder[1]) \
           + Setup.BrickSize

def get_ball_rect(pos):
    return pos + Setup.BallSize

def get_color_rects():
    clrr = []
    y = 0
    colors = [Color.blue, Color.red, Color.green, Color.yellow, Color.white]
    for num_lines, color in zip(Setup.BrickGroupSizes, colors):
        pxl_height = num_lines * (Setup.BrickSize[1] + 2 * Setup.BrickBorder[1])
        clrr += [(color, (0, y, Setup.BoardSize[0], pxl_height))]
        y += pxl_height
    return clrr

class Gamestate:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.pad_pos = (Setup.PaddleLimit[1] + Setup.PaddleLimit[0]) / 2
        self.brick_matrix = [ [i] * Setup.BricksPerLine for i in Setup.BrickStartupPattern ]
        self.score = 0
        self.throw_ball()

    def throw_ball(self):
        self.speed = 1
        self.ball = (random.randint(0, Setup.BoardSize[0]-1), Setup.BoardSize[1]/2)
        self.ball_collisions = False
        self.ball_vector = vector_from_angle((random.random() * 4 + 7) * math.pi / 6, self.speed)


class App:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode(Setup.DisplaySize, 0)
        self.surface = pygame.Surface(Setup.BoardSize)
        self.state = Gamestate()
        self._prepare_color_overlay()

    def _prepare_color_overlay(self):
        self.color_overlay = pygame.Surface(Setup.BoardSize)
        self.color_overlay.fill(Color.white)
        for color, rect in get_color_rects():
            pygame.draw.rect(self.color_overlay, color, rect)

    def stop(self):
        pygame.quit()
        sys.exit()

    def loop(self):
        pass

    def render(self):
        self.surface.fill(Color.black)

        # draw bricks
        row_idx = 0
        for row in self.state.brick_matrix:
            col_idx = 0
            for col in row:
                if col:
                    pygame.draw.rect(self.surface, Color.white, get_brick_rect(row_idx, col_idx))
                    #pygame.draw.rect(self.surface, Color.white, (x+1, y+1, Setup.BrickSize[0], Setup.BrickSize[1]))
                col_idx += 1
            row_idx += 1

        # draw paddle
        pygame.draw.rect(self.surface, Color.white, get_paddle_rect(self.state.pad_pos))

        # draw ball
        pygame.draw.rect(self.surface, Color.white, get_ball_rect(self.state.ball))

        # colors, yay!
        # the overlay will cause the moving ball change color, just like it should
        self.surface.blit(self.color_overlay, (0, 0), special_flags = BLEND_MULT)

        # stretch the image to the whole display
        pygame.transform.scale(self.surface, Setup.DisplaySize, self.display)
        pygame.display.update()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
            self.loop()
            self.render()


if __name__ == '__main__':
    app = App()
    app.run()

