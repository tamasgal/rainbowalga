# coding=utf-8
# Filename: app.py
"""
RainbowAlga

Usage:
    rainbowalga [options] EVENT_FILE
    rainbowalga (-h | --help)
    rainbowalga --version

Options:
    EVENT_FILE         Event file (currently only EVT).
    -h --help          Show this screen.
    -v --version       Show version.
    -d FILE            Detector file (DETX).
    -t MIN_TOT         ToT threshold in ns [default=30].

"""
from __future__ import division, absolute_import, print_function

import time
import pickle
import os

from OpenGL.GLUT import (glutCreateWindow, glutDisplayFunc, glutIdleFunc,
                         glutInit, glutInitDisplayMode, glutInitWindowPosition,
                         glutInitWindowSize, glutKeyboardFunc, glutMainLoop,
                         glutMotionFunc, glutMouseFunc, glutReshapeFunc,
                         glutReshapeWindow, glutSpecialFunc, glutSwapBuffers,
                         glutGet,
                         GLUT_DOUBLE, GLUT_RGB, GLUT_DEPTH, GLUT_MULTISAMPLE,
                         GLUT_WINDOW_WIDTH, GLUT_WINDOW_HEIGHT,
                         GLUT_LEFT_BUTTON, GLUT_DOWN, GLUT_KEY_LEFT,
                         GLUT_KEY_RIGHT)
from OpenGL.GLU import gluPerspective
from OpenGL.GL import (glBegin, glClear, glClearColor, glClearDepth, glColor3f,
                       glDisable, glDisableClientState, glDrawArrays,
                       glDrawPixels, glEnable, glEnableClientState, glEnd,
                       glFrustum, glLightfv, glLoadIdentity, glMaterialfv,
                       glMatrixMode, glOrtho, glPointSize, glPopMatrix,
                       glPushMatrix, glRasterPos, glReadPixels, glShadeModel,
                       glUseProgram, glVertex2f, glVertexPointerf, glViewport,
                       glGetString, GLubyte,
                       GL_PROJECTION, GL_DEPTH_BUFFER_BIT,
                       GL_COLOR_BUFFER_BIT, GL_LIGHT0, GL_NORMALIZE,
                       GL_COLOR_MATERIAL, GL_LIGHTING, GL_AMBIENT, GL_DIFFUSE,
                       GL_SPECULAR, GL_POSITION, GL_FRONT, GL_SHININESS,
                       GL_VERSION, GL_VERTEX_SHADER, GL_FRAGMENT_SHADER,
                       GL_VERTEX_ARRAY, GL_POINTS, GL_DEPTH_TEST,
                       GL_LINE_SMOOTH, GL_FLAT, GL_MODELVIEW, GL_CULL_FACE,
                       GL_QUADS, GL_RGB, GL_UNSIGNED_BYTE)
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import compileShader, compileProgram


import numpy as np
import pylab

from PIL import Image

from rainbowalga.tools import Clock, Camera, draw_text_2d, draw_text_3d
from rainbowalga.physics import Particle, ParticleFit, Neutrino, Hit
from rainbowalga import constants
from rainbowalga import version

from km3pipe.dataclasses import Position
from km3pipe.hardware import Detector
from km3pipe.pumps import EvtPump


class RainbowAlga(object):
    def __init__(self, detector_file=None, event_file=None, min_tot=None,
                 width=800, height=600, x=112, y=84):
        self.camera = Camera()
        self.camera.is_rotating = True

        current_path = os.path.dirname(os.path.abspath(__file__))

        if not detector_file:
            detector_file = os.path.join(current_path,
                                         'data/km3net_jul13_90m_r1494.detx')

        image_path = os.path.join(current_path, 'images/km3net_logo.bmp')
        self.logo = Image.open(image_path)
        # Create a raw string from the image data - data will be unsigned bytes
        # RGBpad, no stride (0), and first line is top of image (-1)
        self.logo_bytes = self.logo.tobytes("raw", "RGB", 0, -1)

        self.init_opengl(width=width, height=height, x=x, y=y)

        print("OpenGL Version: {0}".format(glGetString(GL_VERSION)))
        self.clock = Clock(speed=100)
        self.timer = Clock(snooze_interval=1/30)
        self.frame_index = 0
        self.event_index = 0
        self.is_recording = False
        self.min_tot = min_tot

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

        self.blob = None
        self.objects = []
        self.shaded_objects = []

        self.mouse_x = None
        self.mouse_y = None

        self.show_help = False
        self._help_string = None
        self.show_info = True

        self.spectrum = None
        self.cmap = pylab.get_cmap("gist_rainbow")

        self.detector = Detector(detector_file)
        dom_positions = self.detector.dom_positions
        min_z = min([z for x, y, z in dom_positions])
        max_z = max([z for x, y, z in dom_positions])
        z_shift = (max_z - min_z) / 2
        self.dom_positions = np.array([tuple(pos) for pos in dom_positions], 'f')
        self.camera.target = Position((0, 0, z_shift))
        self.dom_positions_vbo = vbo.VBO(self.dom_positions)

        self.pump = EvtPump(filename=event_file)
        self.load_blob(0)

        self.clock.reset()
        self.timer.reset()
        glutMainLoop()

    def load_blob(self, index=0):
        print("Loading blob {0}...".format(index))
        blob = self.blob = self.pump.get_blob(index)

        self.objects = []
        self.shaded_objects = []

        self.add_neutrino(blob)
        self.add_mc_tracks(blob)
        self.add_reco_tracks(blob)

        hits = blob['EvtRawHits']
        print("Number of hits: {0}".format(len(hits)))
        if self.min_tot:
            hits = [hit for hit in blob['EvtRawHits'] if hit.tot >= self.min_tot]
            print("Number of hits after ToT={0} cut: {1}"
                  .format(self.min_tot, len(hits)))
        if not self.min_tot and len(hits) > 500:
            print("Warning: consider applying a ToT filter to reduce the "
                  "amount of hits, according to your graphic cards "
                  "performance!")

        pmt_hit_map = {}
        for hit in hits:
            pmt_hit_map.setdefault(hit.pmt_id, []).append(hit)
        hits = []
        for pmt_id, pmt_hits in pmt_hit_map.iteritems():
            last_hit = None
            for hit in pmt_hits:
                if last_hit:
                    if hit.tot > last_hit.tot:
                        hits.append(hit)
                else:
                    hits.append(hit)
                last_hit = hit
        print("Number of hits after removing hidden ones: {0}".format(len(hits)))


        hit_times = []
        #step_size = int(len(hits) / 100) + 1
        for hit in hits:
            hit_times.append(hit.time)
            x, y, z = self.detector.pmt_with_id(hit.pmt_id).pos
            self.shaded_objects.append(Hit(x, y, z, hit.time, hit.tot))

        def spectrum(time):
            min_time = min(hit_times)
            max_time = max(hit_times)
            diff = max_time - min_time
            one_percent = diff/100
            try:
                progress = (time - min_time) / one_percent / 100
            except ZeroDivisionError:
                progress = 0
            return tuple(self.cmap(progress))[:3]
        self.spectrum = spectrum

    def add_neutrino(self, blob):
        """Add the neutrino to the scene."""
        try:
            neutrino = blob['Neutrino']
        except KeyError:
            return
        print(neutrino)
        pos = Position((neutrino.pos.x, neutrino.pos.y, neutrino.pos.z + 405.93))
        particle = Neutrino(pos.x, pos.y, pos.z,
                            neutrino.dir.x, neutrino.dir.y, neutrino.dir.z,
                            0)
        particle.color = (1.0, 0.0, 0.0)
        particle.line_width = 3
        self.objects.append(particle)

    def add_mc_tracks(self, blob):
        """Find MC particles and add them to the objects to render."""
        try:
            track_ins = blob['TrackIns']
        except KeyError:
            return

        highest_energetic_track = max(track_ins, key=lambda t: t.E)
        for track in track_ins:
            particle = Particle(track.pos.x, track.pos.y, track.pos.z + 405.93,
                                track.dir.x, track.dir.y, track.dir.z,
                                track.time, constants.c, track.length)
            if track.id == highest_energetic_track.id:
                particle.color = (0.0, 0.0, 1.0)
                particle.line_width = 3
            self.objects.append(particle)

    def add_reco_tracks(self, blob):
        """Find reco particles and add them to the objects to render."""
        try:
            track_fits = blob['TrackFits']
        except KeyError:
            return
        for track in track_fits:
            if not int(track.id) == 314:
                continue
            particle = ParticleFit(track.pos.x, track.pos.y,
                                   track.pos.z + 405.93,
                                   track.dir.x, track.dir.y, track.dir.z,
                                   constants.c, track.ts, track.te)
            print("Found track fit: {0}".format(track))
            self.objects.append(particle)

    def load_next_blob(self):
        try:
            self.load_blob(self.event_index + 1)
        except IndexError:
            return
        else:
            self.clock.reset()
            self.event_index += 1

    def load_previous_blob(self):
        try:
            self.load_blob(self.event_index - 1)
        except IndexError:
            return
        else:
            self.clock.reset()
            self.event_index -= 1


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

        if self.is_recording and not self.timer.is_snoozed:
            self.frame_index += 1
            frame_name = "Frame_{0:05d}.jpg".format(self.frame_index)
            self.save_screenshot(frame_name)
            self.timer.snooze()


        glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.camera.is_rotating:
            self.camera.rotate_z(0.2)
        self.camera.look()

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
        logo = self.logo
        logo_bytes = self.logo_bytes

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

        if self.show_info:
            self.display_info()


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
                self.camera.is_rotating = False
            else:
                self.camera.is_rotating = True

        if button == 3:
            self.camera.distance = self.camera.distance + 2
        if button == 4:
            self.camera.distance = self.camera.distance - 2

    def keyboard(self, key,  x,  y):
        if(key == "r"):
            self.clock.reset()
        if(key == "h"):
            self.show_help = not self.show_help
        if(key == 'i'):
            self.show_info = not self.show_info
        if(key == "+"):
            self.camera.distance = self.camera.distance - 50
        if(key == "-"):
            self.camera.distance = self.camera.distance + 50

        if(key == 'n'):
            self.load_next_blob()

        if(key == 'p'):
            self.load_previous_blob()

        if(key == "s"):
            self.save_screenshot()

        if(key == 'v'):
            self.frame_index = 0
            self.is_recording = not self.is_recording
        if(key == " "):
            if self.clock.is_paused:
                self.clock.resume()
            else:
                self.clock.pause()
        if(key in ('q', chr(27))):
            raise SystemExit

    def special_keyboard(self, key, x, z):
        if key == GLUT_KEY_LEFT:
            self.clock.rewind(100)
        if key == GLUT_KEY_RIGHT:
            self.clock.fast_forward(100)

    def drag(self, x, y):
        self.camera.rotate_z(self.mouse_x - x)
        self.camera.move_z(-(self.mouse_y - y)*8)
        self.mouse_x = x
        self.mouse_y = y

    def save_screenshot(self, name='screenshot.png'):
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        pixelset = (GLubyte * (3*width*height))(0)
        glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixelset)
        image = Image.fromstring(mode="RGB", size=(width, height), data=pixelset)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(name)
        print("Screenshot saved as '{0}'.".format(name))


    @property
    def help_string(self):
        if not self._help_string:
            options = {
                'h': 'help',
                'i': 'show event info',
                'n': 'next event',
                'p': 'previous event',
                'LEFT': '+100ns',
                'RIGHT': '-100ns',
                's': 'save screenshot (screenshot.png)',
                'v': 'start/stop recording (Frame_XXXXX.jpg)',
                'r': 'reset time',
                '<space>': 'pause time',
                '+': 'zoom in',
                '-': 'zoom out',
                '<esc> or q': 'quit',
                }
            help_string = "Keyboard commands:\n-------------------\n"
            for key in sorted(options.keys()):
                help_string += "{key:>10} : {description}\n" \
                               .format(key=key, description=options[key])
            self._help_string = help_string
        return self._help_string

    @property
    def blob_info(self):
        if not self.blob:
            return ''
        info_text = ''
        try:
            event_number = self.blob['start_event'][0]
            info_text += "Event #{0}\n".format(event_number)
        except KeyError:
            pass
        try:
            neutrino = self.blob['Neutrino']
            info_text += str(neutrino)
        except KeyError:
            pass
        return info_text

    def display_help(self):
        pos_y = glutGet(GLUT_WINDOW_HEIGHT) - 80
        draw_text_2d(self.help_string, 10, pos_y)

    def display_info(self):
        draw_text_2d(self.blob_info, 150, 30)


def main():
    from docopt import docopt
    arguments = docopt(__doc__, version=version)
    event_file = arguments['EVENT_FILE']
    detector_file = arguments['-d']
    try:
        min_tot = float(arguments['-t'])
    except TypeError:
        min_tot = 30 
    app = RainbowAlga(detector_file, event_file, min_tot)

 

if __name__ == "__main__":
    main()
