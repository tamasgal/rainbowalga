#!/usr/bin/env python
import sys
import numpy as np
import time
from PyQt5 import QtGui, QtOpenGL
import PyQt5.QtCore as QC
import PyQt5.QtWidgets as QW
import OpenGL.GL as GL
import OpenGL.GLU as GLU
import OpenGL.arrays as GLA

import km3pipe as kp

DOM_POSITIONS = np.array([
    tuple(pos) for pos in kp.hardware.Detector(
        filename="../rainbowalga/data/km3net_jul13_90m_r1494_corrected.detx").
    dom_positions.values()
], 'f')
CAM_TARGET = np.mean(DOM_POSITIONS, axis=0)


class Camera(object):
    def __init__(self, target=np.array([0, 0, 0]), distance=1500):
        self.target = np.array([0, 0, 0])
        self.distance = distance
        self.up = np.array([0, 0, 1])
        self._pos = np.array([1, 0, 1])

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
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GLU.gluLookAt(self.pos[0], self.pos[1], self.pos[2], self.target[0],
                      self.target[1], self.target[2], self.up[0], self.up[1],
                      self.up[2])


class MainWindow(QW.QWidget):
    def __init__(self):
        super(QW.QWidget, self).__init__()

        self.gl_widget = MainCanvas()

        self.slider = self.create_slider()
        self.slider.valueChanged.connect(self.set_dom_color)

        layout = QW.QHBoxLayout()
        layout.addWidget(self.gl_widget)
        layout.addWidget(self.slider)
        self.setLayout(layout)

        self.setWindowTitle("RainbowAlga")

    def set_dom_color(self, value):
        self.gl_widget.dom_color = np.array([0.1, value / 100, 0.5, 1.0])

    def create_slider(self):
        slider = QW.QSlider(QC.Qt.Vertical)

        slider.setRange(0, 100)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setTickInterval(10)
        slider.setTickPosition(QW.QSlider.TicksRight)

        return slider


class MainCanvas(QW.QGLWidget):
    def __init__(self, parent=None):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)

        super(QW.QGLWidget, self).__init__(fmt, None)

        self.camera = Camera(target=CAM_TARGET, distance=500)

        self.t = time.time()
        self._update_timer = QC.QTimer()
        self._update_timer.timeout.connect(self.update)
        self._update_timer.start(1e3 / 60.)

        self.dom_color = np.array([0.3, 0.5, 0.8, 1.0])

    def get_opengl_info(self):
        info = """
            Vendor: {0}
            Renderer: {1}
            OpenGL Version: {2}
            Shader Version: {3}
        """.format(GL.glGetString(GL.GL_VENDOR),
                   GL.glGetString(GL.GL_RENDERER),
                   GL.glGetString(GL.GL_VERSION),
                   GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION))
        return info

    def initializeGL(self):
        print(self.get_opengl_info())

        shader_program = QtGui.QOpenGLShaderProgram()
        vertex_src = """
        #version 410 core
        layout (location = 0) in vec3 dom_pos
        void main() {
            // gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
            gl_Position = gl_ModelViewProjectionMatrix * dom_pos;
        }"""
        fragment_src = """
        #version 410 core
        uniform vec4 u_Color;
        void main() {
            gl_FragColor = u_Color;
        }
        """
        shader_program.addShaderFromSourceCode(QtGui.QOpenGLShader.Vertex,
                                               vertex_src)
        shader_program.addShaderFromSourceCode(QtGui.QOpenGLShader.Fragment,
                                               fragment_src)
        shader_program.link()
        self._shader_program = shader_program

        self.dom_positions_vbo = GLA.vbo.VBO(DOM_POSITIONS)

        GL.glClearDepth(1.0)
        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)

    def minimumSizeHint(self):
        return QC.QSize(100, 100)

    def sizeHint(self):
        return QC.QSize(500, 500)

    def paintGL(self):
        # GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        # GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        self.camera.look()
        self.camera.rotate_z(0.1)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self._shader_program.bind()

        location = GL.glGetUniformLocation(self._shader_program.programId(),
                                           "u_Color")
        GL.glUniform4f(location, *self.dom_color)

        self.dom_positions_vbo.bind()
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glVertexPointerf(self.dom_positions_vbo)
        # GL.glVertexAttribPointer(0, len(DOM_POSITIONS), GL.GL_FLOAT,
        #                          GL.GL_FALSE, 3 * 4, 0)
        # GL.glEnableVertexAttribArray(0)

        GL.glPointSize(2)
        GL.glDrawArrays(GL.GL_POINTS, 0, len(DOM_POSITIONS) * 3)
        self.dom_positions_vbo.unbind()
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glUseProgram(0)

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)


def main():
    app = QW.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
