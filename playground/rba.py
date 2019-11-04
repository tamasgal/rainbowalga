#!/usr/bin/env python
import sys
import numpy as np
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

        VERTEX_SHADER = compile_vertex_shader("""
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }""")
        FRAGMENT_SHADER = compile_fragment_shader("""
        void main() {
            gl_FragColor = vec4(0.5, 0.5, 0.5, 1);
        }""")

        self.program = link_shader_program(VERTEX_SHADER, FRAGMENT_SHADER)

        gl.glClearDepth(1.0)
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 3000)

        # Lighting
        light_ambient = (0.0, 0.0, 0.0, 1.0)
        light_diffuse = (1.0, 1.0, 1.0, 1.0)
        light_specular = (1.0, 1.0, 1.0, 1.0)
        light_position = (-100.0, 100.0, 100.0, 0.0)

        mat_ambient = (0.7, 0.7, 0.7, 1.0)
        mat_diffuse = (0.8, 0.8, 0.8, 1.0)
        mat_specular = (1.0, 1.0, 1.0, 1.0)
        high_shininess = (100)

        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_NORMALIZE)
        gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glEnable(gl.GL_LIGHTING)

        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, light_ambient)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, light_diffuse)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, light_specular)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_position)

        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT, mat_ambient)
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_DIFFUSE, mat_diffuse)
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_SPECULAR, mat_specular)
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_SHININESS, high_shininess)

        # Transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.dom_positions_vbo = gla.vbo.VBO(DOM_POSITIONS)

        # Camera
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        glu.gluLookAt(100, 0, 0, CAM_TARGET[0], CAM_TARGET[1], CAM_TARGET[2],
                      0, 0, 1)

    def minimumSizeHint(self):
        return qc.QSize(100, 100)

    def sizeHint(self):
        return qc.QSize(500, 500)

    def paintGL(self):
        # gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Camera
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        glu.gluLookAt(100, 0, 0, CAM_TARGET[0], CAM_TARGET[1], CAM_TARGET[2],
                      0, 0, 1)

        self.draw_detector()

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glShadeModel(gl.GL_FLAT)
        gl.glEnable(gl.GL_LIGHTING)

        gl.glDisable(gl.GL_LIGHTING)

    def resizeGL(self, width, height):
        side = min(width, height)
        if side < 0:
            return

        gl.glViewport((width - side) // 2, (height - side) // 2, side, side)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def draw_detector(self):
        # check https://github.com/ChrisBeaumont/opengl_sandbox/blob/master/shader_demo.py
        gl.glUseProgram(self.program)
        self.dom_positions_vbo.bind()
        # gl.glEnableVertexAttribArray(0)
        # gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        #
        # gl.glDrawArrays(gl.GL_POINTS, 0, 3)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointerf(self.dom_positions_vbo)
        gl.glPointSize(20)
        gl.glDrawArrays(gl.GL_POINTS, 0, len(DOM_POSITIONS) * 3)
        self.dom_positions_vbo.unbind()
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glUseProgram(0)


def compile_vertex_shader(source):
    """Compile a vertex shader from source."""
    vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(vertex_shader, source)
    gl.glCompileShader(vertex_shader)
    # check compilation error
    result = gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS)
    if not (result):
        raise RuntimeError(gl.glGetShaderInfoLog(vertex_shader))
    return vertex_shader


def compile_fragment_shader(source):
    """Compile a fragment shader from source."""
    fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(fragment_shader, source)
    gl.glCompileShader(fragment_shader)
    # check compilation error
    result = gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS)
    if not (result):
        raise RuntimeError(gl.glGetShaderInfoLog(fragment_shader))
    return fragment_shader


def link_shader_program(vertex_shader, fragment_shader=None):
    """Create a shader program with from compiled shaders."""
    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertex_shader)
    if fragment_shader is not None:
        gl.glAttachShader(program, fragment_shader)
    gl.glLinkProgram(program)
    # check linking error
    result = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
    if not (result):
        raise RuntimeError(gl.glGetProgramInfoLog(program))
    return program


def main():
    app = qw.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
