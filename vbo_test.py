import time
import pickle

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import *

import numpy as np

from PIL import Image

from rainbowalga.tools import Clock, Camera, draw_text_2d, draw_text_3d
from rainbowalga.core import Position

camera = Camera()
camera.is_rotating = True
camera._pos = np.array((1, 1, 1))

logo = Image.open('km3net_logo.bmp')
# Create a raw string from the image data - data will be unsigned bytes
# RGBpad, no stride (0), and first line is top of image (-1)
logo_bytes = logo.tobytes("raw", "RGB", 0, -1)

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





class TestContext(object):
    def __init__(self):   
        glutInit()
        glutInitWindowPosition(112, 84)
        glutInitWindowSize(800, 600)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
        glutCreateWindow("narf")
        glutDisplayFunc(self.render)
        glutIdleFunc(self.render)
        glutReshapeFunc(self.resize)
        
        glutMouseFunc(self.mouse)
        glutMotionFunc(self.drag)
        glutKeyboardFunc(self.keyboard)
        glutSpecialFunc(self.special_keyboard)
        
        glClearDepth(1.0)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)
        glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)

        print("OpenGL Version: {0}".format(glGetString(GL_VERSION)))
        self.clock = Clock(speed=100)

        VERTEX_SHADER = compileShader("""
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }""", GL_VERTEX_SHADER)
        FRAGMENT_SHADER = compileShader("""
        void main() {
            gl_FragColor = vec4(0.8, 0.8, 0.8, 1);
        }""", GL_FRAGMENT_SHADER)
        
        self.shader = compileProgram(VERTEX_SHADER, FRAGMENT_SHADER)
        
        self.triangles = vbo.VBO(
            np.array([
                [0.4, 1, 1],
                [-1, -1, 0],
                [1, -1, 0],
                [2, -1, 0],
                [4, -1, 0],
                [4, 1, 0],
                [2, -1, 0],
                [4, 1, 0],
                [2, 1, 0],
                [0, 0, 0],
                [1, 1, 1],
                [-1, 0, 2]
                ], 'f')
            )
        self.coordsys = vbo.VBO(
            np.array([
                [-1, 0, 0],
                [1, 0, 0],
                [0, -1, 0],
                [0, 1, 0],
                [0, 0, -1],
                [0, 0, 1]
                ], 'f')
            )

        omkeys = pickle.load(open('geometry_dump.pickle', 'r'))
        doms = [pmt for pmt in omkeys.items() if pmt[0][2] == 0]
        self.dom_positions = np.array([pos for omkey, (pos, dir) in doms], 'f')
        self.min_z = min([z for x, y, z in self.dom_positions])
        self.max_z = max([z for x, y, z in self.dom_positions])
        #self.line_positions_lower = [pos for omkey, (pos, dir) in doms
        #                             if omkey[1] == 1 and omkey[2] == 0]
        #self.line_positions_upper = [(x, y, self.max_z) for x, y, z in self.line_positions_lower]
        #self.line_positions = zip(self.line_positions_lower, self.line_positions_upper)

        self.dom_positions_vbo = vbo.VBO(self.dom_positions)
        #self.line_positions_vbo = vbo.VBO(self.line_positions)


        particle = Particle(-100, -100, -100, 1, 0, 0, 1)
        particle2 = Particle(-100, -100, -100, 0.9, 0.3, 0, 1)

        self.objects = [particle, particle2]

        self.mouse_x = None
        self.mouse_y = None

        self.clock.reset()
        glutMainLoop()
        
    def render(self):
        self.clock.record_frame_time()
        if not self.clock.is_snoozed:
            glutSetWindowTitle("FPS: {0:.1f}".format(self.clock.fps));
            self.clock.snooze()

        glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if camera.is_rotating:
            camera.rotate_z(0.2)
        camera.look()

        glUseProgram(self.shader)
        try:
            self.dom_positions_vbo.bind()
            try:
                glEnableClientState(GL_VERTEX_ARRAY)
                glVertexPointerf(self.dom_positions_vbo)
                #glDrawArrays(GL_TRIANGLES, 0, 12)
                glPointSize(2)
                glDrawArrays(GL_POINTS, 0, len(self.dom_positions)*3)
            finally:
                self.dom_positions_vbo.unbind()
                glDisableClientState(GL_VERTEX_ARRAY)
        finally:
            glUseProgram(0)

        for obj in self.objects:
            obj.draw(self.clock.time)


        # 2D stuff
        menubar_height = logo.size[1] 
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, width, height, 0.0, -1.0, 10.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_CULL_FACE)

        glClear(GL_DEPTH_BUFFER_BIT)

        glBegin(GL_QUADS)
        glColor3f(0.14, 0.49, 0.87)
        glVertex2f(0, 0)
        glVertex2f(width-logo.size[0], 0)
        glVertex2f(width-logo.size[0], menubar_height)
        glVertex2f(0, menubar_height)
        glEnd()

        glPushMatrix()
        glLoadIdentity()
        glRasterPos(width-logo.size[0], logo.size[1])
        glDrawPixels(logo.size[0], logo.size[1], GL_RGB, GL_UNSIGNED_BYTE, logo_bytes)
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        draw_text_2d("FPS:  {0:.1f}\nTime: {1:.0f} ns"
                     .format(self.clock.fps, self.clock.time),
                     10, 30)


        glutSwapBuffers()

    def resize(self, width, height):
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(width)/float(height), 0.1, 10000.0)
        glMatrixMode(GL_MODELVIEW)


    def mouse(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            if state == GLUT_DOWN:
                self.mouse_x = x
                self.mouse_y = y
                camera.is_rotating = False
            else:
                camera.is_rotating = True

        if button == 3:
            camera.distance = camera.distance + 1
        if button == 4:
            camera.distance = camera.distance - 1
            
    def keyboard(self, key,  x,  y):
        print("Key pressed: '{0}'".format(key))
        if(key == "r"):
            self.clock.reset()
        if(key == " "):
            if self.clock.is_paused:
                self.clock.resume()
            else:
                self.clock.pause()
        if(key == chr(27)):
            raise SystemExit

    def special_keyboard(self, key, x, z):
        print("Special key pressed: '{0}'".format(key))
        if key == GLUT_KEY_LEFT:
            print("Left key pressed")

    def drag(self, x, y):
        camera.rotate_z(self.mouse_x - x)
        camera.move_z(-(self.mouse_y - y)*5)
        self.mouse_x = x
        self.mouse_y = y

            
if __name__ == "__main__":
    tc = TestContext()
