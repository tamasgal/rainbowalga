from OpenGL.GL import *
from OpenGL.GLUT import *

class Particle(object):
    def __init__(self, x, y, z, dx, dy, dz, speed):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.speed = speed

    def draw(self, time, line_width=3, color=(1.0, 0.0, 0.6)):
        glPushMatrix()
        glLineWidth(line_width)
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex3f(self.x, self.y, self.z)
        glVertex3f(self.x + time * self.dx,
                   self.y + time * self.dy,
                   self.z + time * self.dz)
        glEnd()
        glPopMatrix()


class Hit(object):
    def __init__(self, x, y, z, time):
        self.x = x
        self.y = y
        self.z = z
        self.time = time

    def draw(self, time):
        if time < self.time:
            return
        color = (1.0, 1.0-self.time/3000.0, self.time/3000.0)
        glPushMatrix()
        glTranslated(self.x, self.y, self.z)

        glColor3f(*color)
        #glEnable(GL_COLOR_MATERIAL)
        #glColorMaterial(GL_FRONT, GL_DIFFUSE)
        glutSolidSphere(15, 16, 16)
        #glDisable(GL_COLOR_MATERIAL)


        glPopMatrix()
