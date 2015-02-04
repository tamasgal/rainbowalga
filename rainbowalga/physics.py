from __future__ import division, absolute_import, print_function

import numpy as np

from km3pipe.dataclasses import Position, Direction

from OpenGL.GL import (glPushMatrix,glLineWidth, glColor3f, glBegin, GL_LINES,
                       glEnd, glVertex3f, glPushMatrix, glPopMatrix,
                       glTranslated)
from OpenGL.GLUT import glutSolidSphere


class Particle(object):
    def __init__(self, x, y, z, dx, dy, dz, time, speed,
                 length=None, color=(1.0, 0.0, 0.6)):
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
        self.length = abs(length)
        self.color = color

    def draw(self, time, line_width=2):
        time = time * 1e-9

        pos_start = self.pos + (self.speed * (-self.time) * self.dir)
        path = (self.speed * (time - self.time) * self.dir)
        if self.length:
            max_path = self.length * self.dir
            if np.linalg.norm(max_path) <= np.linalg.norm(path):
                path = max_path
        pos_end = self.pos + path

        glPushMatrix()
        glLineWidth(line_width)
        glColor3f(*self.color)
        glBegin(GL_LINES)
        glVertex3f(*pos_start)
        glVertex3f(*pos_end)
        glEnd()
        glPopMatrix()


class ParticleFit(object):
    def __init__(self, x, y, z, dx, dy, dz, speed, ts, te,
                 color=(1.0, 1.0, 0.6)):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.pos = Position((x, y, z))
        self.dir = Direction((dx, dy, dz))
        self.speed = speed
        self.ts = ts
        self.te = te
        self.color = color

    def draw(self, time, line_width=3):
        if time <= self.ts:
            return
        time = time * 1e-9

        pos_start = self.pos
        path = (self.speed * (time - self.ts * 1e-9) * self.dir)
        #max_end = self.pos + (self.speed * self.te * self.dir)
        #if not int(self.te) == 0 and time > self.te:
        #    pos_end = max_end
        #else:
        #    pos_end = self.pos + path
        pos_end = self.pos + path

        glPushMatrix()
        glLineWidth(line_width)
        glColor3f(*self.color)
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
