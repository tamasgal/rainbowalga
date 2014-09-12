from __future__ import division, absolute_import, print_function

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
from rainbowalga.physics import Particle, Hit
from rainbowalga import constants

camera = Camera()
camera.is_rotating = True

logo = Image.open('km3net_logo.bmp')
# Create a raw string from the image data - data will be unsigned bytes
# RGBpad, no stride (0), and first line is top of image (-1)
logo_bytes = logo.tobytes("raw", "RGB", 0, -1)



class RainbowAlga(object):
    def __init__(self, width=800, height=600, x=112, y=84):

        self.init_opengl(width=width, height=height, x=x, y=y)

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


        self.objects = []
        self.shaded_objects = []

        omkeys = pickle.load(open('geometry_dump.pickle', 'r'))
        doms = [pmt for pmt in omkeys.items() if pmt[0][2] == 0]
        self.dom_positions = np.array([pos for omkey, (pos, dir) in doms], 'f')
        self.min_z = min([z for x, y, z in self.dom_positions])
        self.max_z = max([z for x, y, z in self.dom_positions])

        self.dom_positions_vbo = vbo.VBO(self.dom_positions)


        muon = pickle.load(open('muon_sample.pickle', 'r'))
        muon_pos = muon[0]
        muon_dir = muon[1]

        particle = Particle(muon_pos[0], muon_pos[1], muon_pos[2],
                            muon_dir[0], muon_dir[1], muon_dir[2], constants.c)
        self.objects.append(particle)

        pmt_hits = pickle.load(open('hits_sample.pickle', 'r'))
        hits = [((omkey[0], omkey[1], 0), time) for omkey, time in pmt_hits]
        hits.sort(key=lambda x: x[1])
        unique_omkeys = []
        hit_times = []
        for omkey, hit_time in hits:
            if len(self.shaded_objects) > 100:
                break 
            if not omkey in unique_omkeys:
                unique_omkeys.append(omkey)
                x, y, z = omkeys[omkey][0]
                hit_times.append(hit_time)
                self.shaded_objects.append(Hit(x, y, z, hit_time))

        def spectrum(time):
            min_time = min(hit_times)
            max_time = max(hit_times)
            diff = max_time - min_time
            one_percent = diff/100
            progress = (time - min_time) / one_percent / 100
            return (1, 1-progress, progress)
        self.spectrum = spectrum

        self.mouse_x = None
        self.mouse_y = None

        self.show_help = False
        self._help_string = None

        self.clock.reset()
        glutMainLoop()
        

    def init_opengl(self, width, height, x, y):
        glutInit()
        glutInitWindowPosition(x, y)
        glutInitWindowSize(width, height)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
        glutCreateWindow("Rainbow Alga")
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


        # Lighting
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


    def render(self):
        self.clock.record_frame_time()

        glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if camera.is_rotating:
            camera.rotate_z(0.2)
        camera.look()

        self.draw_detector()

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)
        glShadeModel(GL_FLAT)
        glEnable(GL_LIGHTING)
        
        for obj in self.shaded_objects:
            obj.draw(self.clock.time, self.spectrum)

        glDisable(GL_LIGHTING)

        for obj in self.objects:
            obj.draw(self.clock.time)

        self.draw_gui()


        glutSwapBuffers()

    def draw_detector(self):
        glUseProgram(self.shader)
        try:
            self.dom_positions_vbo.bind()
            try:
                glEnableClientState(GL_VERTEX_ARRAY)
                glVertexPointerf(self.dom_positions_vbo)
                glPointSize(2)
                glDrawArrays(GL_POINTS, 0, len(self.dom_positions)*3)
            finally:
                self.dom_positions_vbo.unbind()
                glDisableClientState(GL_VERTEX_ARRAY)
        finally:
            glUseProgram(0)


    def draw_gui(self):
        menubar_height = logo.size[1] + 4
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
        glVertex2f(width - logo.size[0] - 10, 0)
        glVertex2f(width - logo.size[0] - 10, menubar_height)
        glVertex2f(0, menubar_height)
        glEnd()

        glPushMatrix()
        glLoadIdentity()
        glRasterPos(width - logo.size[0] - 4, logo.size[1] + 2)
        glDrawPixels(logo.size[0], logo.size[1], GL_RGB, GL_UNSIGNED_BYTE, logo_bytes)
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glColor3f(1.0, 1.0, 1.0)

        draw_text_2d("FPS:  {0:.1f}\nTime: {1:.0f} ns"
                     .format(self.clock.fps, self.clock.time),
                     10, 30)
        if self.show_help:
            self.display_help()


    def resize(self, width, height):
        if width < 400:
            glutReshapeWindow(400, height)
        if height < 300:
            glutReshapeWindow(width, 300)
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
            camera.distance = camera.distance + 2
        if button == 4:
            camera.distance = camera.distance - 2
            
    def keyboard(self, key,  x,  y):
        print("Key pressed: '{0}'".format(key))
        if(key == "r"):
            self.clock.reset()
        if(key == "h"):
            self.show_help = not self.show_help
        if(key == "+"):
            camera.distance = camera.distance - 50
        if(key == "-"):
            camera.distance = camera.distance + 50

        if(key == "s"):
            self.save_screenshot()
        if(key == " "):
            if self.clock.is_paused:
                self.clock.resume()
            else:
                self.clock.pause()
        if(key in ('q', chr(27))):
            raise SystemExit

    def special_keyboard(self, key, x, z):
        print("Special key pressed: '{0}'".format(key))
        if key == GLUT_KEY_LEFT:
            print("Left key pressed")

    def drag(self, x, y):
        camera.rotate_z(self.mouse_x - x)
        camera.move_z(-(self.mouse_y - y)*8)
        self.mouse_x = x
        self.mouse_y = y

    def save_screenshot(self):
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        pixelset = (GLubyte * (3*width*height))(0)
        glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixelset)
        image = Image.fromstring(mode="RGB", size=(width, height), data=pixelset)     
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save('screenshot.png')
        print("Screenshot saved as 'screenshot.png'.")


    @property
    def help_string(self):
        if not self._help_string:
            options = {
                'h': 'help',
                'r': 'reset time',
                's': 'save screenshot (screenshot.png)',
                '<space>': 'pause time',
                '<esc> or q': 'quit',
                '+': 'zoom in',
                '-': 'zoom out'
                }
            help_string = "Keyboard commands:\n-------------------\n"
            for key in sorted(options.keys()):
                help_string += "{key:>10} : {description}\n" \
                               .format(key=key, description=options[key])
            self._help_string = help_string
        return self._help_string

    def display_help(self):
        pos_y = glutGet(GLUT_WINDOW_HEIGHT) - 80
        draw_text_2d(self.help_string, 10, pos_y)


if __name__ == "__main__":
    app = RainbowAlga()
