from __future__ import division, absolute_import, print_function

import pickle

from OpenGL.GLUT import glutSolidSphere
from OpenGL.GL import (glBegin, glColor3f, glColorMaterial, glDisable,
                       glEnable, glEnd, glLineWidth, glPointSize, glPopMatrix,
                       glPushMatrix, glShadeModel, glTranslated, glVertex3f,
                       GL_POINTS, GL_LINES, GL_DEPTH_TEST, GL_FLAT,
                       GL_LIGHTING, GL_COLOR_MATERIAL, GL_FRONT, GL_DIFFUSE)

from .core import Position

class Detector(object):
    def __init__(self):
        omkeys = pickle.load(open('geometry_dump.pickle', 'r')) 
        self.doms = [pmt for pmt in omkeys.items() if pmt[0][2] == 0]
        self.dom_positions = [pos for omkey, (pos, dir) in self.doms]
        self.line_positions = [pos for omkey, (pos, dir) in self.doms
                                   if omkey[1] == 1 and omkey[2] == 0]
        self.z_min = min([z for x, y, z in self.dom_positions])
        self.z_max = max([z for x, y, z in self.dom_positions])

    def draw_lines(self, line_width=1):
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_FLAT)
        for position in self.line_positions:
            glPushMatrix()
            glTranslated(position[0], position[1], 0)
            glLineWidth(line_width)
            glBegin(GL_LINES)
            glVertex3f(0.0, 0.0, self.z_min)
            glVertex3f(0.0, 0.0, self.z_max)
            glEnd()
            glPopMatrix()

    def draw_doms(self, size=3):
        glPushMatrix()
        glPointSize(size)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_POINTS)
        for position in self.dom_positions:
            glVertex3f(position[0], position[1], position[2])
        glEnd()
        glPopMatrix()



class DetectorLine(object):
    def __init__(self, x, y, z, length):
        self.x = x
        self.y = y
        self.z = z 
        self.length = length
        
    def draw(self, line_width=2):
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_FLAT)
        glPushMatrix()
        glTranslated(self.x, self.y, self.z)
        glLineWidth(line_width)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, self.length)
        glEnd()
        glPopMatrix()


class DOM(object):
    def __init__(self, pos=Position(0, 0, 0), radius=0.2):
        self.pos = pos
        self.radius = radius

    def draw(self):
        glPushMatrix()
        glTranslated(self.pos.x, self.pos.y, self.pos.z)

        glEnable(GL_LIGHTING)
        color_r = 0.5
        color_g = 0.0
        color_b = 0.0
        glColor3f(color_r, color_g, color_b)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT, GL_DIFFUSE)
        #glDisable(GL_TEXTURE_2D)
        glutSolidSphere(self.radius, 64, 64)
        glDisable(GL_COLOR_MATERIAL)

        glDisable(GL_LIGHTING)

        glPopMatrix()
