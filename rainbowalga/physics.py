from __future__ import division, absolute_import, print_function

import numpy as np

from km3pipe import constants
from km3pipe.dataclasses import Position, Direction

from OpenGL.GL import (glPushMatrix,glLineWidth, glColor3f, glBegin, GL_LINES,
                       glEnd, glVertex3f, glPushMatrix, glPopMatrix, glEnable,
                       glTranslated, glRotated, GL_FLAT, GL_DEPTH_TEST,
                       glShadeModel, glDisable, GL_LIGHTING, glMultMatrixf,
                       glColor4f)
from OpenGL.GLUT import glutSolidSphere, glutSolidCone

from rainbowalga.gui import Colourist

class Neutrino(object):
    def __init__(self, x, y, z, dx, dy, dz, time,
                 color=(1.0, 0.0, 0.0), line_width=3):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.pos = Position((x, y, z))
        self.dir = Direction((dx, dy, dz))
        self.start_pos = Position((x, y, z)) - self.dir*1000
        self.time = time * 1e-9
        self.color = color
        self.line_width = line_width
        self.hidden = False

    def draw(self, time, line_width=None):
        if self.hidden:
            return
        time = time * 1e-9


        pos_start = self.start_pos + (constants.c * (-self.time) * self.dir)
        if time >= self.time:
            pos_end = self.pos
        else:
            path = (constants.c * (time - self.time) * self.dir)
            pos_end = self.pos + path

        glPushMatrix()
        glLineWidth(self.line_width)
        glColor3f(*self.color)
        glBegin(GL_LINES)
        glVertex3f(*pos_start)
        glVertex3f(*pos_end)
        glEnd()
        glPopMatrix()

class Particle(object):
    def __init__(self, x, y, z, dx, dy, dz, time, speed, colourist,
                 energy, length=0, color=(0.0, 0.5, 0.7), line_width=1,
                 cherenkov_cone_enabled=False):
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
        self.energy = energy
        self.length = abs(length)
        self.color = color
        self.line_width = line_width
        self.cherenkov_cone_enabled = cherenkov_cone_enabled
        self.colourist = colourist
        self.hidden = False

    def draw(self, time, line_width=None):
        if self.hidden:
            return
        time = time * 1e-9
        if time <= self.time:
            return

        pos_start = self.pos + (self.speed * (-self.time) * self.dir)
        path = (self.speed * (time - self.time) * self.dir)
        if self.length:
            max_path = self.length * self.dir
            if np.linalg.norm(max_path) <= np.linalg.norm(path):
                path = max_path
        pos_end = self.pos + path



        glPushMatrix()
        if line_width:
            glLineWidth(line_width)
        else:
            glLineWidth(self.line_width)
        glColor3f(*self.color)
        glBegin(GL_LINES)
        glVertex3f(*pos_start)
        glVertex3f(*pos_end)
        glEnd()
        glPopMatrix()

        if self.cherenkov_cone_enabled and \
                self.colourist.cherenkov_cone_enabled:

            height = np.linalg.norm(pos_end - pos_start)
            position = pos_end - self.dir * height

            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)
            glShadeModel(GL_FLAT)
            glColor4f(0.0, 0.0, 0.8, 0.3)

            glPushMatrix()
            glTranslated(*position)
            glPushMatrix()

            v = np.array(self.dir)
            glMultMatrixf(transform(v))

            glutSolidCone(0.6691*height, height, 128, 64)
            glPopMatrix()
            glPopMatrix()
            
            glDisable(GL_LIGHTING)


class ParticleFit(object):
    def __init__(self, x, y, z, dx, dy, dz, speed, ts, te,
                 color=(1.0, 1.0, 0.6), line_width=2):
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
        self.line_width = line_width
        self.hidden = False

    def draw(self, time, line_width=None):
        if self.hidden:
            return
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
        if line_width:
            glLineWidth(line_width)
        else:
            glLineWidth(self.line_width)
        glColor3f(*self.color)
        glBegin(GL_LINES)
        glVertex3f(*pos_start)
        glVertex3f(*pos_end)
        glEnd()
        glPopMatrix()


class Hit(object):
    def __init__(self, x, y, z, time, pmt_id, hit_id, tot=10, replaces_hits=None):
        self.x = x
        self.y = y
        self.z = z
        self.time = time
        self.tot = tot
        self.pmt_id = pmt_id
        self.hidden = False
        self.t_cherenkov = None
        self.replaces_hits = replaces_hits

    def _hide_replaced_hits(self):
        if self.replaces_hits:
            for hit in self.replaces_hits:
                hit.hidden = True

    def _show_replaced_hits(self):
        if self.replaces_hits:
            for hit in self.replaces_hits:
                hit.hidden = False

    def draw(self, time, spectrum):
        if self.hidden:
            return
        if time < self.time:
            self._show_replaced_hits()
            return

        self._hide_replaced_hits()

        #color = (1.0, 1.0-self.time/2000.0, self.time/2000.0)
        color = spectrum(self.time, self)
        glPushMatrix()
        glTranslated(self.x, self.y, self.z)

        glColor3f(*color)
        #glEnable(GL_COLOR_MATERIAL)
        #glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glutSolidSphere(int(1+np.sqrt(self.tot)*1.5), 16, 16)
        #glDisable(GL_COLOR_MATERIAL)


        glPopMatrix()


def normalize(v):
    norm = np.linalg.norm(v)
    if norm > 1.0e-8:  # arbitrarily small
        return v/norm
    else:
        return v

def transform(v):
    bz = normalize(v)
    if (abs(v[2]) < abs(v[0])) and (abs(v[2]) < abs(v[1])):
        by = normalize(np.array([v[1], -v[0], 0]))
    else:
        by = normalize(np.array([v[2], 0, -v[0]]))
        #~ by = normalize(np.array([0, v[2], -v[1]]))

    bx = np.cross(by, bz)
    R =  np.array([[bx[0], by[0], bz[0], 0],
                   [bx[1], by[1], bz[1], 0],
                   [bx[2], by[2], bz[2], 0],
                   [0,     0,     0,     1]], dtype=np.float32)

    return R.T
