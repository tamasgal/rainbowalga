from __future__ import division, absolute_import, print_function

import time

import numpy as np

from OpenGL.GLUT import (glutGet, GLUT_WINDOW_WIDTH, GLUT_WINDOW_HEIGHT,
                         glutBitmapCharacter, GLUT_BITMAP_8_BY_13,
                         glutSolidCone)
from OpenGL.GLU import gluLookAt
from OpenGL.GL import (glMatrixMode, GL_MODELVIEW, glBegin, glEnd, glEnable,
                       GL_DEPTH_TEST, glLoadIdentity, GL_PROJECTION,
                       GL_PROJECTION_MATRIX, glGetDouble, glPushMatrix,
                       glPopMatrix, glVertex3f, glLineWidth, glOrtho,
                       glColor3f, glRasterPos, glRasterPos2i, GL_LINE_SMOOTH,
                       GL_FLAT, GL_LINES, glTranslated, glRotated)

from .core import Position


class Clock(object):
    """This class controls the time of the whole simulation.

    :param float speed: Scale factor for simulation times
    :param float snooze_interval: Seconds to be snoozed

    """
    def __init__(self, speed=1, snooze_interval=1):
        self.speed = speed
        self.snooze_interval = snooze_interval
        self._global_offset = 0
        self.reset()

    @property
    def time(self):
        """Return the elapsed time since offset."""
        if self.is_paused:
            current_time = self.paused_at
        else:
            current_time = self.unix_time()
        return (current_time - self.offset + self._global_offset) * self.speed

    def rewind(self, time):
        self.offset += time / self.speed

    def fast_forward(self, time):
        self.offset -= time / self.speed


    def reset(self):
        """Set the offset to now."""
        now = self.unix_time()
        self.is_paused = False
        self.offset = now
        self.snooze_time = now
        self.frame_times = []

    def pause(self):
        self.is_paused = True
        self.paused_at = self.unix_time()

    def resume(self):
        self.is_paused = False
        now = self.unix_time()
        paused_time = now - self.paused_at
        self.offset += paused_time

    def unix_time(self):
        """Return seconds since epoch."""
        return time.time()

    def record_frame_time(self):
        """Save the frame time for FPS calculations (keep only the last 10)."""
        if len(self.frame_times) > 10:
            del(self.frame_times[0])
        self.frame_times.append(self.unix_time())

    def snooze(self):
        """Set the snooze time to now"""
        self.snooze_time = self.unix_time()

    @property
    def is_snoozed(self):
        """Check if still snoozed"""
        return self.unix_time() - self.snooze_time < self.snooze_interval

    @property
    def fps(self):
        """Frames per second calculated from recorded frame times"""
        try:
            times = self.frame_times
            return (len(times) - 1) / (times[-1] - times[0])
        except (ZeroDivisionError, IndexError):
            return 0


class Camera(object):
    """The camera. Desperately needs refactoring."""
    def __init__(self, distance=1500, up=Position(0, 0, 1)):
        self.target = Position(0, 0, 0)
        self.up = up
        self._pos = np.array((1, 1, 1))
        self.distance = distance
        self.is_rotating = False

    @property
    def pos(self):
        self._pos = self._pos / np.linalg.norm(self._pos)
        current_position = self._pos * self.distance
        return Position(current_position[0], current_position[1], current_position[2])

    def rotate_y(self, angle):
        theta = angle * np.pi / 180
        rotation_matrix = np.matrix([[np.cos(theta), 0, np.sin(theta)],
                                     [0, 1, 0],
                                     [-np.sin(theta),  -0, np.cos(theta)]])
        new_position = rotation_matrix.dot(self._pos)
        self._pos = np.array((new_position[0, 0], new_position[0, 1], new_position[0, 2]))

    def rotate_z(self, angle):
        theta = angle * np.pi / 180
        rotation_matrix = np.matrix([[np.cos(theta), -np.sin(theta), 0],
                                     [np.sin(theta),  np.cos(theta), 0],
                                     [0, 0, 1]])
        new_position = rotation_matrix.dot(self._pos)
        self._pos = np.array((new_position[0, 0], new_position[0, 1], new_position[0, 2]))

    def move_z(self, distance):
        position = self.pos
        self._pos = np.array((position.x, position.y, position.z + distance))

    def look(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.pos.x, self.pos.y, self.pos.z,
                  self.target.x, self.target.y, self.target.z,
                  self.up.x, self.up.y, self.up.z)


class CoordinateSystem(object):
    def draw(self, line_width=1, color=(1.0, 0.0, 0.0)):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)
        glShadeModel(GL_FLAT)
        glPushMatrix()
        glLineWidth(line_width)
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(-1.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)
        glEnd()
        glPushMatrix()
        glTranslated(1.0, 0.0, 0.0)
        glRotated(90, 0.0, 1.0, 0.0)
        glutSolidCone(0.05, 0.2, 16, 16)
        glPopMatrix()
        glBegin(GL_LINES)
        glVertex3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        glEnd()
        glPushMatrix()
        glTranslated(0.0, 1.0, 0.0)
        glRotated(-90, 1.0, 0.0, 0.0)
        glutSolidCone(0.05, 0.2, 16, 16)
        glPopMatrix()
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, -1.0)
        glVertex3f(0.0, 0.0, 1.0)
        glEnd()
        glPushMatrix()
        glTranslated(0.0, 0.0, 1.0)
        glutSolidCone(0.05, 0.2, 16, 16)
        glPopMatrix()
        glPopMatrix()

def draw_text_2d(text, x, y, line_height=17, color=None):
    """Draw a text at a given 2D position.

    A very basic 2D drawing function for drawing (multi-line) text."
    """
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix() #matrix = glGetDouble( GL_PROJECTION_MATRIX )
    glLoadIdentity()
    glOrtho(0.0, width, 0.0, height, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    if color:
        glColor3f(*color)
    glRasterPos2i(x, y)
    lines = 0
    for character in text:
        if character == '\n':
            lines += 1
            glRasterPos(x, y - (lines * line_height))
        else:
            glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix() #glLoadMatrixd(matrix)
    glMatrixMode(GL_MODELVIEW)

def draw_text_3d(text, x, y, z, color=None):
    """Draw a text at a given 3D position.

    A very basic 3D drawing function for displaying text in a 3D scene.
    The multi-line support is experimental.
    """
    if color:
        glColor3f(*color)
    glRasterPos(x, y, z)
    for character in text:
        if character == '\n':
            glRasterPos(x, y, z-15)
        else:
            glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))


def base_round(x, base=10):
    return int(base * round(float(x)/base))
