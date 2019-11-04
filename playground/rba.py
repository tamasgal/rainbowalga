#!/usr/bin/env python
import sys
import numpy as np
import time
from PyQt5 import QtGui
import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
import OpenGL.GL as gl
import OpenGL.GLU as glu
import OpenGL.arrays as gla
import OpenGL.GL.shaders as gls

import km3pipe as kp

DOM_POSITIONS = np.array([
    tuple(pos) for pos in kp.hardware.Detector(
        filename="/home/tgal/data/detx/KM3NeT_-00000001_20171212.detx").
    dom_positions.values()
], 'f')
CAM_TARGET = np.mean(DOM_POSITIONS, axis=0)


class Camera(object):
    def __init__(self, target=np.array([0, 0, 0]), distance=1500):
        self.target = np.array([0, 0, 0])
        self.distance = distance
        self.up = np.array([0, 0, 1])
        self._pos = np.array([1, 0, 0])

    @property
    def pos(self):
        self._pos = self._pos / np.linalg.norm(self._pos)
        current_position = self._pos * self.distance
        return np.array(
            [current_position[0], current_position[1], current_position[2]])

    def rotate_z(self, angle):
        theta = angle * np.pi / 180
        rotation_matrix = np.matrix([[np.cos(theta), -np.sin(theta), 0],
                                     [np.sin(theta),
                                      np.cos(theta), 0], [0, 0, 1]])
        new_position = rotation_matrix.dot(self._pos)
        self._pos = np.array(
            [new_position[0, 0], new_position[0, 1], new_position[0, 2]])

    def look(self):
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        glu.gluLookAt(self.pos[0], self.pos[1], self.pos[2], self.target[0],
                      self.target[1], self.target[2], self.up[0], self.up[1],
                      self.up[2])


class MainWindow(qw.QWidget):
    def __init__(self):
        super(qw.QWidget, self).__init__()

        self.gl_widget = MainCanvas()

        layout = qw.QHBoxLayout()
        layout.addWidget(self.gl_widget)
        self.setLayout(layout)

        self.setWindowTitle("RainbowAlga")


class MainCanvas(qw.QOpenGLWidget):
    def __init__(self, parent=None):
        super(qw.QOpenGLWidget, self).__init__(parent)
        self.camera = Camera(target=CAM_TARGET, distance=1500)

        self.t = time.time()
        self._update_timer = qc.QTimer()
        self._update_timer.timeout.connect(self.update)
        self._update_timer.start(1e3 / 60.)

    def get_opengl_info(self):
        info = """
            Vendor: {0}
            Renderer: {1}
            OpenGL Version: {2}
            Shader Version: {3}
        """.format(gl.glGetString(gl.GL_VENDOR),
                   gl.glGetString(gl.GL_RENDERER),
                   gl.glGetString(gl.GL_VERSION),
                   gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION))
        return info

    def initializeGL(self):
        print(self.get_opengl_info())

        shader_program = QtGui.QOpenGLShaderProgram()
        vertex_src = """
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }"""
        fragment_src = """
        void main() {
            gl_FragColor = vec4(0.5, 0.5, 0.5, 1.0);
        }
        """
        shader_program.addShaderFromSourceCode(QtGui.QOpenGLShader.Vertex,
                                               vertex_src)
        shader_program.addShaderFromSourceCode(QtGui.QOpenGLShader.Fragment,
                                               fragment_src)
        shader_program.link()
        self._shader_program = shader_program

        self.dom_positions_vbo = gla.vbo.VBO(DOM_POSITIONS)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)

        # gl.glClearDepth(1.0)
        # gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        # gl.glMatrixMode(gl.GL_PROJECTION)
        # gl.glLoadIdentity()
        # gl.glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)
        #
        # # Lighting
        # light_ambient = (0.0, 0.0, 0.0, 1.0)
        # light_diffuse = (1.0, 1.0, 1.0, 1.0)
        # light_specular = (1.0, 1.0, 1.0, 1.0)
        # light_position = (-100.0, 100.0, 100.0, 0.0)
        #
        # mat_ambient = (0.7, 0.7, 0.7, 1.0)
        # mat_diffuse = (0.8, 0.8, 0.8, 1.0)
        # mat_specular = (1.0, 1.0, 1.0, 1.0)
        # high_shininess = (100)
        #
        # gl.glEnable(gl.GL_LIGHT0)
        # gl.glEnable(gl.GL_NORMALIZE)
        # gl.glEnable(gl.GL_COLOR_MATERIAL)
        # gl.glEnable(gl.GL_LIGHTING)
        #
        # gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, light_ambient)
        # gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, light_diffuse)
        # gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, light_specular)
        # gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_position)
        #
        # gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT, mat_ambient)
        # gl.glMaterialfv(gl.GL_FRONT, gl.GL_DIFFUSE, mat_diffuse)
        # gl.glMaterialfv(gl.GL_FRONT, gl.GL_SPECULAR, mat_specular)
        # gl.glMaterialfv(gl.GL_FRONT, gl.GL_SHININESS, high_shininess)
        #
        # # Transparency
        # gl.glEnable(gl.GL_BLEND)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def minimumSizeHint(self):
        return qc.QSize(100, 100)

    def sizeHint(self):
        return qc.QSize(500, 500)

    def paintGL(self):
        # gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        # gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        self.camera.look()
        self.camera.rotate_z(0.1)
        # GLU.gluLookAt(1, 0, 0, *CAM_TARGET, 0, 0, 1)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._shader_program.bind()
        self.dom_positions_vbo.bind()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointerf(self.dom_positions_vbo)
        gl.glPointSize(2)
        gl.glDrawArrays(gl.GL_POINTS, 0, len(DOM_POSITIONS) * 3)
        self.dom_positions_vbo.unbind()
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glUseProgram(0)

    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        # side = min(width, height)
        # if side < 0:
        #     return
        #
        # gl.glViewport((width - side) // 2, (height - side) // 2, side, side)
        #
        # gl.glMatrixMode(gl.GL_PROJECTION)
        # gl.glLoadIdentity()
        # gl.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
        # gl.glMatrixMode(gl.GL_MODELVIEW)

    # def draw_detector(self):
    #     # check https://github.com/ChrisBeaumont/opengl_sandbox/blob/master/shader_demo.py
    #     gl.glUseProgram(self.program)
    #     self.dom_positions_vbo.bind()
    #     # gl.glEnableVertexAttribArray(0)
    #     # gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    #     #
    #     # gl.glDrawArrays(gl.GL_POINTS, 0, 3)
    #
    #     gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    #     gl.glVertexPointerf(self.dom_positions_vbo)
    #     gl.glPointSize(20)
    #     gl.glDrawArrays(gl.GL_POINTS, 0, len(DOM_POSITIONS) * 3)
    #     self.dom_positions_vbo.unbind()
    #     gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    #     gl.glUseProgram(0)


def main():
    app = qw.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # import time
    #
    # while True:
    #     time.sleep(0.1)
    #     window.gl_widget.paintGL()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
