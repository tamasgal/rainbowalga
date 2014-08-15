from __future__ import division
import time

import numpy as np

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from .core import Position


class Clock(object):
    """This class controls the time of the whole simulation.
    
    :param float speed: Scale factor for simulation times
    :param float snooze_interval: Seconds to be snoozed

    """
    def __init__(self, speed=1, snooze_interval=1):
        self.speed = speed
        self.snooze_interval = snooze_interval
        self.reset()

    @property
    def time(self):
        """Return the elapsed time since offset."""
        return (self.unix_time() - self.offset) * self.speed

    def reset(self):
        """Set the offset to now."""
        now = self.unix_time()
        self.offset = now
        self.snooze_time = now
        self.frame_times = []

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
    def snoozed(self):
        """Check if still snoozed"""
        return self.unix_time() - self.snooze_time < self.snooze_interval

    @property
    def fps(self):
        """Frames per second calculated from recorded frame times"""
        try:
            times = self.frame_times
            return len(times) / (times[-1] - times[0])
        except (ZeroDivisionError, IndexError):
            return 0


class Camera(object):
    def __init__(self, distance=1):
        self.target = Position(0, 0, 0)
        self.up = Position(0, 0, 1)
        self._pos = np.array((1, 1, 1))
        self.distance = distance
        
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

