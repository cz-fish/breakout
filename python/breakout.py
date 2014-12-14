#!/usr/bin/env python

import pygame, sys
from pygame.locals import *
import random
import math

class Setup:
    DisplaySize = (800, 600)
    FPS = 60

    PaddleLimit = (0, 1024)
    PaddleSpeed = int((PaddleLimit[1] - PaddleLimit[0])/(0.9 * FPS))
    BallSpeed = 2.75
    BoardSize = (320, 240)
    BrickStartupPattern = ([1]*4 + [0]*2)*3 + [0]*(4+2)*2
    BrickGroupSizes = [6, 6, 6, 6, 6]
    BrickLines = sum(BrickGroupSizes)

# 10 bricks per line: width 30, border 1, margin 0
# 16 bricks per line: width 18, border 1, margin 0
# 20 bricks per line: width 14, border 1, margin 0
# 4 lines per group: height 5, border 1, margin 0, paddletop 222
# 5 lines per group: height 4, border 1, margin 0, paddletop 222
    BricksPerLine = 16
    BrickSize = (18, 5)
    BrickBorder = (1, 1)
    BallSize = (4, 4)
    PaddleSize = (30, 4)
    PaddleTop = 222
    BoardMargin = (0, 0)


class Color:
    black = (0, 0, 0)
    white = (255, 255, 255)
    blue = (0, 0, 170)
    red = (153, 0, 0)
    green = (0, 204, 0)
    yellow = (255, 235, 0)
    gray = (60, 60, 60)


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

def get_brick_index(pos):
    row = (pos[1] - Setup.BoardMargin[1]) / (Setup.BrickSize[1] + 2 * Setup.BrickBorder[1])
    if row >= Setup.BrickLines:
        return None
    col = (pos[0] - Setup.BoardMargin[0]) / (Setup.BrickSize[0] + 2 * Setup.BrickBorder[0])
    return (int(row), int(col))

def get_ball_rect(pos):
    return (int(pos[0]), int(pos[1])) + Setup.BallSize

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
        self.stopped = True
        self.has_ball = False

    def throw_ball(self):
        self.speed = Setup.BallSpeed
        self.ball = (random.randint(0, Setup.BoardSize[0]-1), Setup.BoardSize[1]/3.0)
        self.ball_collisions = False
        self.ball_vector = vector_from_angle((random.random() * 4 + 7) * math.pi / 6, self.speed)
        self.has_ball = True

    def tick(self):
        if self.stopped:
            return
        if not self.has_ball:
            self.throw_ball()

        newball = (self.ball[0] + self.ball_vector[0], self.ball[1] + self.ball_vector[1])
        newball = self.bounce(newball)
        newball = self.collide(newball)
        self.ball = newball

    def bounce(self, newball):
        x = newball[0]
        y = newball[1]
        revert_x = False
        revert_y = False

        max_x = Setup.BoardSize[0] - Setup.BallSize[0]
        if x < 0:
            x = -x
            revert_x = True
        elif x > max_x:
            x = 2 * max_x - x
            revert_x = True

        # do not bouce off the bottom edge
        if y < 0:
            y = -y
            revert_y = True

        self.ball_vector = ([self.ball_vector[0], -self.ball_vector[0]][revert_x], \
                            [self.ball_vector[1], -self.ball_vector[1]][revert_y])
        return (x, y)

    def collide(self, newball):
        if newball[1] >= Setup.PaddleTop - Setup.BallSize[1]:
            return self.collide_with_paddle(newball)
        # collide with bricks
        if not self.ball_collisions:
            # ball is in ghost mode after it has been thrown.
            # no collisions with bricks until it hits the paddle
            return newball
        brick_index = get_brick_index(newball)
        if brick_index:
            return self.collide_with_bricks(newball, brick_index)
        # no collision
        return newball

    def collide_with_paddle(self, newball):
        collision_y = Setup.PaddleTop - Setup.BallSize[1]
        collision_x = self.ball[0] + (collision_y - self.ball[1]) * self.ball_vector[0] / self.ball_vector[1]
        
        ball_x_middle = collision_x + Setup.BallSize[0] / 2.0
        paddle = get_paddle_rect(self.pad_pos)
        # cushion of 1 ball size around the paddle from each side
        big_paddle_left = paddle[0] - Setup.BallSize[0]
        big_paddle_right = big_paddle_left + Setup.PaddleSize[0] + 2 * Setup.BallSize[0]
        big_paddle_third = (big_paddle_right - big_paddle_left) / 3.0

        if ball_x_middle < big_paddle_left or ball_x_middle > big_paddle_right:
            # ball dropped
            self.ball_dropped()
            return newball
        else:
            # ball bounces off paddle
            if ball_x_middle < big_paddle_left + big_paddle_third:
                # left end of the paddle. Angle in second quadrant based on collision position
                v = (ball_x_middle - big_paddle_left) / big_paddle_third
                angle = (math.pi * 11/12) - v * math.pi / 3
                self.ball_vector = vector_from_angle(angle, self.speed)
            elif ball_x_middle < big_paddle_left + 2 * big_paddle_third:
                # middle part of the paddle. Angle preserved
                self.ball_vector = (self.ball_vector[0], -self.ball_vector[1])
            else:
                # right end of the paddle. Angle in first quadrant based on collision position
                v = (big_paddle_right - ball_x_middle) / big_paddle_third
                angle = (math.pi * 1/12) + v * math.pi / 3
                self.ball_vector = vector_from_angle(angle, self.speed)
            # deactivate ball ghost mode after first bounce
            self.ball_collisions = True
            return (collision_x, collision_y)

    def collide_with_bricks(self, newball, brick_index_topleft):
        # because the ball is bigger than a pixel, it can collide with up to 4 bricks.
        # we need to select just one brick to collide with
        brick_index_bottomright = get_brick_index((newball[0] + Setup.BallSize[0], newball[1] + Setup.BallSize[1]))
        if not brick_index_bottomright or brick_index_topleft == brick_index_bottomright:
            colliding_brick_indices = [brick_index_topleft]
        else:
            row_min = brick_index_topleft[0]
            row_max = brick_index_bottomright[0]
            col_min = brick_index_topleft[1]
            col_max = brick_index_bottomright[1]
            if row_min != row_max:
                # either bottom row first or top row first based on the ball vector direction
                rows = [ [row_min, row_max], # ball is going down
                         [row_max, row_min]  # ball is going up
                       ] [self.ball_vector[1] < 0]
            else:
                rows = [row_min]
            if col_min != col_max:
                # either left first or right first based on the ball vector direction
                cols = [ [col_min, col_max], # ball is going right
                         [col_max, col_min]  # ball is going left
                       ] [self.ball_vector[0] < 0]
            else:
                cols = [col_min]
            colliding_brick_indices = [(row, col) for row in rows for col in cols]

        for row, col in colliding_brick_indices:
            if self.brick_matrix[row][col]:
                return self.collide_with_brick(newball, row, col)
        # none of the potentially colliding bricks exists in the matrix, no collision
        return newball

    def collide_with_brick(self, newball, row, col):
        brick = get_brick_rect(row, col)
        brick_bbox = (brick[0] - Setup.BallSize[0], # left
                      brick[1] - Setup.BallSize[1], # top
                      brick[0] + brick[2],          # right
                      brick[1] + brick[3])          # bottom

        # first assume that the collision was on the top or the bottom edge
        if self.ball_vector[1] > 0:
            # ball going down, collision spot is the top edge of the brick
            collision_y = brick_bbox[1]
        else:
            # ball going up, collision spot is the bottom edge of the brick
            collision_y = brick_bbox[3]
        collision_x = self.ball[0] + (collision_y - self.ball[1]) * self.ball_vector[0] / self.ball_vector[1]

        if collision_x >= brick_bbox[0] and collision_x <= brick_bbox[2]:
            # the collision was indeed on one of the horizontal edges
            # switch the vertical direction, keep horizontal direction
            self.ball_vector = (self.ball_vector[0], -self.ball_vector[1])
        else:
            # the collision was actually on a vertical edge
            if collision_x < brick_bbox[0]:
                collision_x = brick_bbox[0]
            else:
                collision_x = brick_bbox[2]
            collision_y = self.ball[1] + (collision_x - self.ball[0]) * self.ball_vector[1] / self.ball_vector[0]
            # switch the horizontal direction, keep vertical direction
            self.ball_vector = (-self.ball_vector[0], self.ball_vector[1])

        self.brick_matrix[row][col] = 0
        # TODO: score, speed, drop bricks, etc.
        return (collision_x, collision_y)

    def ball_dropped(self):
        self.has_ball = False
        self.stopped = True

class KeyboardController:
    def __init__(self):
        self.key_left = False
        self.key_right = False

    def up(self, key):
        if key == pygame.K_LEFT:
            self.key_left = False
        elif key == pygame.K_RIGHT:
            self.key_right = False

    def down(self, key):
        if key == pygame.K_LEFT:
            self.key_left = True
        elif key == pygame.K_RIGHT:
            self.key_right = True

    def move_paddle(self, current_pos):
        if not (self.key_left ^ self.key_right):
            return current_pos
        if self.key_left:
            return max(Setup.PaddleLimit[0], current_pos - Setup.PaddleSpeed)
        else:
            return min(Setup.PaddleLimit[1], current_pos + Setup.PaddleSpeed)

class PotController:
    def move_paddle(self, current_pos):
        # TODO
        return current_pos

class App:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode(Setup.DisplaySize, 0)
        pygame.display.set_caption("Breakout")
        self.surface = pygame.Surface(Setup.BoardSize)
        self.state = Gamestate()
        self._prepare_color_overlay()

        self.kbd_controller = KeyboardController()
        self.pot_controller = PotController()
        self.clock = pygame.time.Clock()

    def _prepare_color_overlay(self):
        self.color_overlay = pygame.Surface(Setup.BoardSize)
        self.color_overlay.fill(Color.white)
        for color, rect in get_color_rects():
            pygame.draw.rect(self.color_overlay, color, rect)

    def stop(self):
        pygame.quit()
        sys.exit()

    def loop(self):
        self.clock.tick(Setup.FPS)
        paddle_pos = self.state.pad_pos
        paddle_pos = self.kbd_controller.move_paddle(paddle_pos)
        paddle_pos = self.pot_controller.move_paddle(paddle_pos)
        self.state.pad_pos = paddle_pos
        self.state.tick()

    def render(self):
        self.surface.fill(Color.black)

        # a bottom bar for better orientation
        pygame.draw.rect(self.surface, Color.gray, (0, Setup.PaddleTop, Setup.BoardSize[0], Setup.BoardSize[1]))

        # draw bricks
        row_idx = 0
        for row in self.state.brick_matrix:
            col_idx = 0
            for col in row:
                if col:
                    pygame.draw.rect(self.surface, Color.white, get_brick_rect(row_idx, col_idx))
                col_idx += 1
            row_idx += 1

        # draw paddle
        pygame.draw.rect(self.surface, Color.white, get_paddle_rect(self.state.pad_pos))

        # draw ball
        if self.state.has_ball:
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
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        self.state.stopped = not self.state.stopped
                    elif event.key == pygame.K_ESCAPE:
                        self.stop()
                    else:
                        self.kbd_controller.up(event.key)
                elif event.type == pygame.KEYDOWN:
                    self.kbd_controller.down(event.key)

            self.loop()
            self.render()


if __name__ == '__main__':
    app = App()
    app.run()

