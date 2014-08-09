from __future__ import division

import sys
import math

import numpy as np

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

class CoordinateSystem(object):
    def draw(self, line_width=1, color=(1.0, 0.0, 0.0)):
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_FLAT)
        glPushMatrix()
        glLineWidth(line_width)
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(-1.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, -1.0)
        glVertex3f(0.0, 0.0, 1.0)
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
        glLineWidth(line_width)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, self.length, 0.0)
        glEnd()
        glPopMatrix()


detector_line = DetectorLine(0, 0, 0, 5)
coordinate_system = CoordinateSystem()
angle = 0


class Position(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        
class Camera(object):
    def __init__(self, zoom=1):
        self.pos = Position(1, 0, 0)
        self.target = Position(0, 0, 0)
        self.up = Position(0, 1, 0)
        self._zoom = zoom
        self._pos = np.array((self.pos.x, self.pos.y, self.pos.z))
        
    @property
    def zoom(self):
        return self._zoom
        
    @zoom.setter
    def zoom(self, value):
        self._pos = self._pos / np.linalg.norm(self._pos)
        new_position = self._pos * value
        self.pos = Position(new_position[0], new_position[1], new_position[2])
        self._zoom = value
        
    def look(self):
        gluLookAt(self.pos.x, self.pos.y, self.pos.z,
                  self.target.x, self.target.y, self.target.z,
                  self.up.x, self.up.y, self.up.z)
        

camera = Camera(zoom=10)

def draw():
    glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    camera.look()
    coordinate_system.draw()
    detector_line.draw(1)
    
    glutSwapBuffers()


def process_keyboard(key,  x,  y):
    if(key == chr(27)):
        raise SystemExit


def process_special_keys(key, x, z):
    global angle
    if key == GLUT_KEY_LEFT:
        print("rotating left")
        camera.rotate(0.1)

def mouse(button, state, x, y):
    print button, state, x, y
    if button == 3:
        camera.zoom = camera.zoom + 0.1
    if button == 4:
        camera.zoom = camera.zoom - 0.1
    


VOID, RESET, QUIT = range(3)

def reset():
    global camera
    print("Debug...")
    camera = Camera()



def doquit():
    raise SystemExit

menudict ={RESET : reset,  
           QUIT : doquit}

def dmenu(item):
    menudict[item]()
    return 0

if __name__ == "__main__":
    glutInit()
    glutInitWindowPosition(112, 84)
    glutInitWindowSize(800, 600)
    # use multisampling if available 
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
    wintitle = "RainbowAlga"
    glutCreateWindow(wintitle)
    glutDisplayFunc(draw)
    glutIdleFunc(draw)
    glutKeyboardFunc(process_keyboard)
    glutSpecialFunc(process_special_keys)
    glutMouseFunc(mouse)
    
    glutCreateMenu(dmenu)
    glutAddMenuEntry("Debug", RESET)
    glutAddMenuEntry("Quit", QUIT)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    # setup OpenGL state 
    glClearDepth(1.0)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 30)
    glMatrixMode(GL_MODELVIEW)


    # start event processing */
    print 'RIGHT-CLICK to display the menu.'
    glutMainLoop()

