from OpenGL.GL import *

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
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)
        glShadeModel(GL_FLAT)
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
