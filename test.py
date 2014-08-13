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
        glEnable(GL_LINE_SMOOTH)
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



class Position(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        
class Camera(object):
    def __init__(self, distance=1):
        self.target = Position(0, 0, 0)
        self.up = Position(0, 1, 0)
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

    def look(self):
        gluLookAt(self.pos.x, self.pos.y, self.pos.z,
                  self.target.x, self.target.y, self.target.z,
                  self.up.x, self.up.y, self.up.z)
        

class DOM(object):
    def __init__(self, pos=Position(0, 0, 0), radius=0.2):
        self.pos = pos
        self.radius = radius

    def draw(self):
        glPushMatrix()
        glTranslated(self.pos.x, self.pos.y, self.pos.z)

        glEnable(GL_LIGHTING)
        glColor3f(1.0, 0.0, 1.0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glDisable(GL_TEXTURE_2D)
        glutSolidSphere(self.radius, 32, 32)
        glDisable(GL_COLOR_MATERIAL)

        glDisable(GL_LIGHTING)

        glPopMatrix()


camera = Camera(distance=10)
detector_line = DetectorLine(0, 0, 0, 5)
coordinate_system = CoordinateSystem()


doms = []
n = 4
for x in range(n):
    for y in range(n):
        for z in range(n):
            dom = DOM(pos=Position(x - n/2, y - n/2, z - n/2))
            doms.append(dom)

angle = 0


def draw():
    glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    camera.rotate_y(0.1)
    camera.look()
    coordinate_system.draw()
    detector_line.draw(1)
    for dom in doms:
        dom.draw()

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
    #print button, state, x, y
    if button == 3:
        camera.distance = camera.distance + 0.1
    if button == 4:
        camera.distance = camera.distance - 0.1
    


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
    global quadratic
    quadratic = gluNewQuadric()
    gluQuadricNormals(quadratic, GLU_SMOOTH)

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

    light_ambient = (0.0, 0.0, 0.0, 1.0)
    light_diffuse = (1.0, 1.0, 1.0, 1.0)
    light_specular = (1.0, 1.0, 1.0, 1.0)
    light_position = (-100.0, 100.0, 100.0, 0.0)

    mat_ambient = (0.7, 0.7, 0.7, 1.0)
    mat_diffuse = (0.8, 0.8, 0.8, 1.0)
    mat_specular = (1.0, 1.0, 1.0, 1.0)
    high_shininess = (100)

    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR,  light_specular)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)

    glMaterialfv(GL_FRONT, GL_AMBIENT,   mat_ambient)
    glMaterialfv(GL_FRONT, GL_DIFFUSE,   mat_diffuse)
    glMaterialfv(GL_FRONT, GL_SPECULAR,  mat_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, high_shininess)

    # start event processing */
    print 'RIGHT-CLICK to display the menu.'
    glutMainLoop()

