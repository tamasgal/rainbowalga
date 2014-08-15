import time
import pickle

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import *

import numpy as np

from rainbowalga.tools import Clock, Camera
from rainbowalga.core import Position

camera = Camera(distance=10, up=Position(0, 0, 1))
camera._pos = np.array((1, 1, 1))

class TestContext(object):
    def __init__(self):   
        glutInit()
        glutInitWindowPosition(112, 84)
        glutInitWindowSize(800, 600)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_MULTISAMPLE)
        glutCreateWindow("narf")
        glutDisplayFunc(self.Render)
        glutIdleFunc(self.Render)
        glutMouseFunc(self.mouse)
        glClearDepth(1.0)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)
        glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)

        self.clock = Clock()

        VERTEX_SHADER = compileShader("""
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }""", GL_VERTEX_SHADER)
        FRAGMENT_SHADER = compileShader("""
        void main() {
            gl_FragColor = vec4(0, 1, 0, 1);
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
        self.dom_positions_vbo = vbo.VBO(self.dom_positions)
        print self.dom_positions
        print len(self.dom_positions)


        glutMainLoop()
        
    def Render(self):
        self.clock.record_frame_time()
        if not self.clock.snoozed:
            glutSetWindowTitle("FPS: {0:.1f}".format(self.clock.fps));
            self.clock.snooze()

        glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        camera.rotate_z(1)
        camera.look()

        glUseProgram(self.shader)
        try:
            self.dom_positions_vbo.bind()
            try:
                glEnableClientState(GL_VERTEX_ARRAY)
                glVertexPointerf(self.coordsys)
                #glDrawArrays(GL_TRIANGLES, 0, 12)
                glPointSize(2)
                glDrawArrays(GL_POINTS, 0, len(self.dom_positions)*3)
            finally:
                self.dom_positions_vbo.unbind()
                glDisableClientState(GL_VERTEX_ARRAY)
        finally:
            glUseProgram(0)

        glutSwapBuffers()

    def mouse(self, button, state, x, y):
        if button == 3:
            camera.distance = camera.distance + 1
        if button == 4:
            camera.distance = camera.distance - 1
            
            
if __name__ == "__main__":
    tc = TestContext()
