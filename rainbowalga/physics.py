from __future__ import division, absolute_import, print_function

import numpy as np

from km3pipe.dataclasses import Position, Direction

from OpenGL.GL import (glPushMatrix,glLineWidth, glColor3f, glBegin, GL_LINES,
                       glEnd, glVertex3f, glPushMatrix, glPopMatrix,
                       glTranslated)
from OpenGL.GLUT import glutSolidSphere


class Particle(object):
    def __init__(self, x, y, z, dx, dy, dz, time, speed, length=None):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.pos = Position((x, y, z))
        self.dir = Direction((dx, dy, dz))
        self.time = time * 1e-9
        self.speed = speed
        self.length = None

    def draw(self, time, line_width=2, color=(1.0, 0.0, 0.6)):
        time = time * 1e-9

        pos_start = self.pos + (self.speed * (-self.time) * self.dir)
        pos_end = self.pos + (self.speed * (time - self.time) * self.dir)

        glPushMatrix()
        glLineWidth(line_width)
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(*pos_start)
        glVertex3f(*pos_end)
        glEnd()
        glPopMatrix()

class Hit(object):
    def __init__(self, x, y, z, time, tot=10):
        self.x = x
        self.y = y
        self.z = z
        self.time = time
        self.tot = tot

    def draw(self, time, spectrum):
        if time < self.time:
            return
        #color = (1.0, 1.0-self.time/2000.0, self.time/2000.0)
        color = spectrum(self.time)
        glPushMatrix()
        glTranslated(self.x, self.y, self.z)

        glColor3f(*color)
        #glEnable(GL_COLOR_MATERIAL)
        #glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glutSolidSphere(int(1+np.sqrt(self.tot)*1.5), 16, 16)
        #glDisable(GL_COLOR_MATERIAL)


        glPopMatrix()
