# coding=utf-8
# Filename: __main__.py
"""
RainbowAlga

Usage:
    rainbowalga
    rainbowalga [options] [EVENT_FILE]
    rainbowalga (-h | --help)
    rainbowalga --version

Options:
    EVENT_FILE         Event file (currently only EVT).
    -h --help          Show this screen.
    -v --version       Show version.
    -d DETECTOR        Detector file (DETX) or detector ID (eg. D_ARCA003).
    -t MIN_TOT         ToT threshold in ns [default=30].
    -s INDEX           Skip to event at index [default=0].

"""
from __future__ import division, absolute_import, print_function

import time
import pickle
import os
import math
import itertools

from OpenGL.GLUT import (glutCreateWindow, glutDisplayFunc, glutIdleFunc,
                         glutInit, glutInitDisplayMode, glutInitWindowPosition,
                         glutInitWindowSize, glutKeyboardFunc, glutMainLoop,
                         glutMotionFunc, glutMouseFunc, glutReshapeFunc,
                         glutReshapeWindow, glutSpecialFunc, glutSwapBuffers,
                         glutGet,
                         GLUT_DOUBLE, GLUT_RGB, GLUT_DEPTH, GLUT_MULTISAMPLE,
                         GLUT_WINDOW_WIDTH, GLUT_WINDOW_HEIGHT,
                         GLUT_LEFT_BUTTON, GLUT_DOWN, GLUT_UP, GLUT_KEY_LEFT,
                         GLUT_KEY_RIGHT)
from OpenGL.GLU import gluPerspective
from OpenGL.GL import (glBegin, glClear, glClearColor, glClearDepth, glColor3f,
                       glDisable, glDisableClientState, glDrawArrays,
                       glDrawPixels, glEnable, glEnableClientState, glEnd,
                       glFrustum, glLightfv, glLoadIdentity, glMaterialfv,
                       glMatrixMode, glOrtho, glPointSize, glPopMatrix,
                       glPushMatrix, glRasterPos, glReadPixels, glShadeModel,
                       glUseProgram, glVertex2f, glVertexPointerf, glViewport,
                       glGetString, GLubyte, glBlendFunc,
                       GL_PROJECTION, GL_DEPTH_BUFFER_BIT,
                       GL_COLOR_BUFFER_BIT, GL_LIGHT0, GL_NORMALIZE,
                       GL_COLOR_MATERIAL, GL_LIGHTING, GL_AMBIENT, GL_DIFFUSE,
                       GL_SPECULAR, GL_POSITION, GL_FRONT, GL_SHININESS,
                       GL_VERSION, GL_VERTEX_SHADER, GL_FRAGMENT_SHADER,
                       GL_VERTEX_ARRAY, GL_POINTS, GL_DEPTH_TEST,
                       GL_LINE_SMOOTH, GL_FLAT, GL_MODELVIEW, GL_CULL_FACE,
                       GL_QUADS, GL_RGB, GL_UNSIGNED_BYTE, GL_SMOOTH,
                       GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import compileShader, compileProgram


import numpy as np

from PIL import Image

from rainbowalga.tools import Clock, Camera, draw_text_2d, base_round
from rainbowalga.physics import Particle, ParticleFit, Neutrino, Hit
from rainbowalga.gui import Colourist
from rainbowalga import constants
from rainbowalga import version

from km3pipe.dataclasses import Position
from km3pipe.hardware import Detector
from km3pipe.pumps import EvtPump, HDF5Pump
from km3pipe.tools import pdg2name, angle_between
from km3pipe import constants

from km3pipe.logger import logging
log = logging.getLogger('rainbowalga')  # pylint: disable=C0103


class RainbowAlga(object):
    def __init__(self, detector_file=None, event_file=None, min_tot=None,
                 skip_to_blob=0,
                 width=1000, height=700, x=50, y=50):
        self.camera = Camera()
        self.camera.is_rotating = True

        self.colourist = Colourist()

        current_path = os.path.dirname(os.path.abspath(__file__))

        if not detector_file:
            detector_file = os.path.join(current_path,
                            'data/km3net_jul13_90m_r1494_corrected.detx')

        self.load_logo()

        self.init_opengl(width=width, height=height, x=x, y=y)

        print("OpenGL Version: {0}".format(glGetString(GL_VERSION)))
        self.clock = Clock(speed=100)
        self.timer = Clock(snooze_interval=1/30)
        self.frame_index = 0
        self.event_index = skip_to_blob
        self.is_recording = False
        self.min_tot = min_tot

        VERTEX_SHADER = compileShader("""
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }""", GL_VERTEX_SHADER)
        FRAGMENT_SHADER = compileShader("""
        void main() {
            gl_FragColor = vec4(0.5, 0.5, 0.5, 1);
        }""", GL_FRAGMENT_SHADER)

        self.shader = compileProgram(VERTEX_SHADER, FRAGMENT_SHADER)


        self.blob = None
        self.objects = {}
        self.shaded_objects = []

        self.mouse_x = None
        self.mouse_y = None

        self.show_secondaries = True
        self.show_help = False
        self._help_string = None
        self.show_info = True

        self.spectrum = None
        self.current_spectrum = 'default'
        self.cmap = self.colourist.default_cmap
        self.min_hit_time = None
        self.max_hit_time = None

        if detector_file.endswith('.detx'):
            self.detector = Detector(filename=detector_file)
        else:
            self.detector = Detector(det_id=detector_file)

        dom_positions = self.detector.dom_positions
        min_z = min([z for x, y, z in dom_positions])
        max_z = max([z for x, y, z in dom_positions])
        z_shift = (max_z - min_z) / 2
        self.dom_positions = np.array([tuple(pos) for pos in dom_positions], 'f')
        self.camera.target = Position((0, 0, z_shift))
        self.dom_positions_vbo = vbo.VBO(self.dom_positions)

        if event_file:
            if event_file.endswith('.evt'):
                ThePump = EvtPump
                self._hits_key = 'EvtRawHits'
                self._mc_tracks_key = 'TrackIns'
            elif event_file.endswith('.h5'):
                ThePump = HDF5Pump
                self._hits_key = 'Hits'
                self._mc_tracks_key = 'MCTracks'
            elif event_file.endswith('.root'):
                from km3pipe.pumps import AanetPump  # noqa
                ThePump = AanetPump
                self._hits_key = 'Hits'
                self._mc_tracks_key = 'MCTracks'
            else:
                log.critical("Filetype not supported: '{0}'".format(event_file))
                raise SystemExit

            self.pump = ThePump(filename=event_file)

            try:
                self.load_blob(skip_to_blob)
            except IndexError:
                print("Could not load blob at index {0}".format(skip_to_blob))
                print("Starting from the first one...")
                self.load_blob(0)
        else:
            print("No event file specified. Only the detector will be shown.")

        self.clock.reset()
        self.timer.reset()
        glutMainLoop()

    def load_logo(self):
        if self.colourist.print_mode:
            image = 'images/km3net_logo_print.bmp'
        else:
            image = 'images/km3net_logo.bmp'

        current_path = os.path.dirname(os.path.abspath(__file__))

        image_path = os.path.join(current_path, image)
        self.logo = Image.open(image_path)
        # Create a raw string from the image data - data will be unsigned bytes
        # RGBpad, no stride (0), and first line is top of image (-1)
        self.logo_bytes = self.logo.tobytes("raw", "RGB", 0, -1)

    def load_blob(self, index=0):
        print("Loading blob {0}...".format(index))
        blob = self.blob = self.pump.get_blob(index)

        self.objects = {}
        self.shaded_objects = []

        try:
            self.add_neutrino(blob)
        except TypeError:
            pass
        self.add_mc_tracks(blob)
        self.add_reco_tracks(blob)

        self.initialise_spectrum(blob, style=self.current_spectrum)

    def reload_blob(self):
        self.load_blob(self.event_index)

    def initialise_spectrum(self, blob, style="default"):

        if style == 'default':
            hits = self.extract_hits(blob)
            hits = self.remove_hidden_hits(hits)

            hit_times = []
            #step_size = int(len(hits) / 100) + 1
            for hit in hits:
                if hit.time > 0:
                    hit_times.append(hit.time)

            if len(hit_times) == 0:
                log.warn("No hits left after applying cuts.")
                return

            self.min_hit_time = min(hit_times)
            self.max_hit_time = max(hit_times)

            self.clock._global_offset = self.min_hit_time / self.clock.speed

            def spectrum(time, hit=None):
                min_time = self.min_hit_time
                max_time = self.max_hit_time
                diff = max_time - min_time
                one_percent = diff/100
                try:
                    progress = (time - min_time) / one_percent / 100
                except ZeroDivisionError:
                    progress = 0
                return tuple(self.cmap(progress))[:3]
            self.spectrum = spectrum

        if style == 'time_residuals_point_source' or style == 'time_residuals_cherenkov_cone':
            try:
                track_ins = blob[self._hits_key]
            except KeyError:
                log.error("No tracks found to determine Cherenkov parameters!")
                self.current_spectrum = "default"
                return
            most_energetic_muon = max(track_ins, key=lambda t: t.E)
            if not pdg2name(most_energetic_muon.particle_type) in ['mu-', 'mu+']:
                log.error("No muon found to determine Cherenkov parameters!")
                self.current_spectrum = "default"
                return


            hits = self.extract_hits(blob)
            hits = self.first_om_hits(hits)

            def cherenkov_time(pmt_pos):
                """Calculates Cherenkov arrival time in [ns]"""
                vertex_pos = most_energetic_muon.pos
                muon_dir = most_energetic_muon.dir

                v = pmt_pos - vertex_pos
                l = v.dot(muon_dir)
                k = np.sqrt(v.dot(v) - l**2)
                v_g = constants.c_water_km3net
                theta = constants.theta_cherenkov_water_km3net
                t_cherenkov = 1/constants.c * (l - k/np.tan(theta)) + 1 /v_g * k/np.sin(theta)
                return t_cherenkov * 1e9

            def point_source_time(pmt_pos):
                """Calculates cherenkov arrival time with cascade hypothesis"""
                vertex_pos = blob['Neutrino'].pos

                v = pmt_pos - vertex_pos
                v = np.sqrt(v.dot(v))
                v_g = constants.c_water_antares
                t_cherenkov = v / v_g
                return t_cherenkov * 1e9 + blob['Neutrino'].time



            self.min_hit_time = -100
            self.max_hit_time = 100

            def spectrum(time, hit=None):
                if hit:
                    pmt_pos = self._get_pmt_pos_from_hit(hit)
                    if not hit.t_cherenkov:
                        if style == 'time_residuals_point_source':
                            t_cherenkov = point_source_time(pmt_pos)
                        elif style == 'time_residuals_cherenkov_cone':
                            t_cherenkov = cherenkov_time(pmt_pos)
                        hit.t_cherenkov = t_cherenkov
                        log.debug("Hit time: {0}, Expected: {1}, Time Residual: {2}"
                              .format(time, t_cherenkov, time - t_cherenkov))
                    time = time - hit.t_cherenkov

                diff = self.max_hit_time - self.min_hit_time
                one_percent = diff/100
                try:
                    progress = (time - self.min_hit_time) / one_percent / 100
                    if progress > 1:
                        progress = 1
                except ZeroDivisionError:
                    progress = 0
                return tuple(self.cmap(progress))[:3]
            self.spectrum = spectrum

    def toggle_spectrum(self):
        if self.current_spectrum == 'default':
            print('cherenkov')
            self.current_spectrum = 'time_residuals_cherenkov_cone'
        elif self.current_spectrum == 'time_residuals_cherenkov_cone':
            print('cherenkov')
            self.current_spectrum = 'time_residuals_point_source'
        else:
            print('default')
            self.current_spectrum = 'default'
        self.reload_blob()

    def remove_hidden_hits(self, hits):
        om_hit_map = {}
        for hit in hits:
            x, y, z = self._get_pmt_pos_from_hit(hit)
            rb_hit = Hit(x, y, z, hit.time, hit.pmt_id, hit.id, hit.tot)
            try:  # EVT file
                line_floor = self.detector.pmtid2omkey(hit.pmt_id)[:2]
            except KeyError:  # Other files
                line, floor, _ = self.detector.doms[hit.dom_id]
                line_floor = line, floor
            om_hit_map.setdefault(line_floor, []).append(rb_hit)
        hits = []
        for om, om_hits in om_hit_map.iteritems():
            largest_hit = None
            for hit in om_hits:
                if largest_hit:
                    if hit.tot > largest_hit.tot:
                        hidden_hits = om_hits[:om_hits.index(hit)]
                        hit.replaces_hits = hidden_hits
                        hits.append(hit)
                        self.shaded_objects.append(hit)
                        largest_hit = hit
                else:
                    hits.append(hit)
                    self.shaded_objects.append(hit)
                    largest_hit = hit
        print("Number of hits after removing hidden ones: {0}"
              .format(len(hits)))
        return hits

    def first_om_hits(self, hits):
        om_hit_map = {}
        for hit in hits:
            if hit.time < 0:
                continue
            x, y, z = self._get_pmt_pos_from_hit(hit)
            rb_hit = Hit(x, y, z, hit.time, hit.pmt_id, hit.id, hit.tot)
            try:  # EVT file
                line_floor = self.detector.pmtid2omkey(hit.pmt_id)[:2]
            except KeyError:  # Other files
                line, floor, _ = self.detector.doms[hit.dom_id]
                line_floor = line, floor
            om_hit_map.setdefault(line_floor, []).append(rb_hit)
        hits = []
        for om, om_hits in om_hit_map.iteritems():
            first_hit = om_hits[0]
            self.shaded_objects.append(first_hit)
            hits.append(first_hit)
        print("Number of first OM hits: {0}".format(len(hits)))
        return hits

    def _get_pmt_pos_from_hit(self, hit):
        try:
            pos = self.detector.pmt_with_id(hit.pmt_id).pos
        except KeyError:
            pos = self.detector.get_pmt(hit.dom_id, hit.channel_id).pos
        return pos

    def extract_hits(self, blob):
        try:
            hits = blob['Hits']
        except KeyError:
            raise SystemExit("No suitable hits found in the file!")

        print("Number of hits: {0}".format(len(hits)))
        if self.min_tot:
            hits = [hit for hit in hits if hit.tot > self.min_tot]
            print("Number of hits after ToT={0} cut: {1}"
                  .format(self.min_tot, len(hits)))
        if not self.min_tot and len(hits) > 500:
            print("Warning: consider applying a ToT filter to reduce the "
                  "amount of hits, according to your graphic cards "
                  "performance!")
        hits.sort(key=lambda h: h.time)
        return hits

    def add_neutrino(self, blob):
        """Add the neutrino to the scene."""
        try:
            neutrino = blob['Neutrino']
        except KeyError:
            return
        print(neutrino)
        pos = Position((neutrino.pos.x, neutrino.pos.y, neutrino.pos.z))
        particle = Neutrino(pos.x, pos.y, pos.z,
                            neutrino.dir.x, neutrino.dir.y, neutrino.dir.z,
                            0)
        particle.color = (1.0, 0.0, 0.0)
        particle.line_width = 3
        self.objects.setdefault("neutrinos", []).append(particle)

    def add_mc_tracks(self, blob):
        """Find MC particles and add them to the objects to render."""
        try:
            track_ins = blob[self._mc_tracks_key]
        except KeyError:
            return

        try:
            highest_energetic_track = max(track_ins, key=lambda t: t.E)
        except ValueError:  # hdf5 mc tracks are not implemented yet
            return
        highest_energy = highest_energetic_track.E
        for track in track_ins:
            if track.particle_type in (0, 22):
                # skip unknowns, photons
                continue
            if angle_between(highest_energetic_track.dir, track.dir) > 0.035:
                # TODO: make this realistic!
                # skip if angle too large
                continue
            if track.particle_type not in (-11, 11, -13, 13, -15, 15):
                # TODO: make this realistic!
                track.length = 200 * track.E / highest_energy
            particle = Particle(track.pos.x, track.pos.y, track.pos.z,
                                track.dir.x, track.dir.y, track.dir.z,
                                track.time, constants.c, self.colourist,
                                track.E, track.length)
            particle.hidden = not self.show_secondaries
            if track.id == highest_energetic_track.id:
                particle.color = (0.0, 1.0, 0.2)
                particle.line_width = 3
                particle.cherenkov_cone_enabled = True
                particle.hidden = False
            self.objects.setdefault("mc_tracks", []).append(particle)

    def add_reco_tracks(self, blob):
        """Find reco particles and add them to the objects to render."""
        try:
            track_fits = blob['TrackFits']
        except (KeyError, TypeError):
            return
        for track in track_fits:
            if not int(track.id) == 314:
                continue
            particle = ParticleFit(track.pos.x, track.pos.y, track.pos.z,
                                   track.dir.x, track.dir.y, track.dir.z,
                                   constants.c, track.ts, track.te)
            print("Found track fit: {0}".format(track))
            self.objects.setdefault("reco_tracks", []).append(particle)

    def toggle_secondaries(self):
        self.show_secondaries = not self.show_secondaries

        secondaries = self.objects["mc_tracks"]
        for secondary in secondaries:
            secondary.hidden = not self.show_secondaries

        highest_energetic = max(secondaries, key=lambda s: s.energy)
        if highest_energetic:
            highest_energetic.hidden = False


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

        # Transparency
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);


    def render(self):
        self.clock.record_frame_time()

        if self.is_recording and not self.timer.is_snoozed:
            self.frame_index += 1
            frame_name = "Frame_{0:05d}.jpg".format(self.frame_index)
            self.save_screenshot(frame_name)
            self.timer.snooze()


        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.colourist.now_background()

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

        for obj in itertools.chain.from_iterable(self.objects.values()):
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
        #glDisable(GL_CULL_FACE)
        glShadeModel(GL_SMOOTH)

        glClear(GL_DEPTH_BUFFER_BIT)

        # Top bar
        #glBegin(GL_QUADS)
        #glColor3f(0.14, 0.49, 0.87)
        #glVertex2f(0, 0)
        #glVertex2f(width - logo.size[0] - 10, 0)
        #glVertex2f(width - logo.size[0] - 10, menubar_height)
        #glVertex2f(0, menubar_height)
        #glEnd()

        try:
            self.draw_colour_legend()
        except TypeError:
            pass

        glPushMatrix()
        glLoadIdentity()
        glRasterPos(4, logo.size[1] + 4)
        glDrawPixels(logo.size[0], logo.size[1], GL_RGB, GL_UNSIGNED_BYTE, logo_bytes)
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        self.colourist.now_text()


        #draw_text_2d("{0}ns".format(int(self.min_hit_time)), width - 80, 20)
        #draw_text_2d("{0}ns".format(int(self.max_hit_time)), width - 80, height - menubar_height - 10)
        #draw_text_2d("{0}ns".format(int((self.min_hit_time + self.max_hit_time) / 2)), width - 80, int(height/2))


        if self.show_help:
            self.display_help()

        if self.show_info:
            self.display_info()

    def draw_colour_legend(self):
        menubar_height = self.logo.size[1] + 4
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        # Colour legend
        left_x = width - 20
        right_x = width - 10
        min_y = menubar_height + 5
        max_y = height - 20
        time_step_size = math.ceil(self.max_hit_time / 20 / 50) * 50
        hit_times = list(range(int(self.min_hit_time), int(self.max_hit_time), int(time_step_size)))
        if len(hit_times) > 1:
            segment_height = int((max_y - min_y) / len(hit_times))
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glDisable(GL_LIGHTING)
            glBegin(GL_QUADS)
            for hit_time in hit_times:
                segment_nr = hit_times.index(hit_time)
                glColor3f(*self.spectrum(hit_time))
                glVertex2f(left_x, max_y - segment_height * segment_nr)
                glVertex2f(right_x, max_y - segment_height * segment_nr)
                glColor3f(*self.spectrum(hit_time + time_step_size))
                glVertex2f(left_x, max_y - segment_height * (segment_nr + 1))
                glVertex2f(right_x, max_y - segment_height * (segment_nr + 1))
            glEnd()

            # Colour legend labels
            self.colourist.now_text()
            for hit_time in hit_times:
                segment_nr = hit_times.index(hit_time)
                draw_text_2d("{0:>5}ns".format(hit_time), width - 80, (height - max_y) + segment_height * segment_nr)

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
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)

        if button == GLUT_LEFT_BUTTON:
            if state == GLUT_DOWN:
                if x > width - 70:
                    self.drag_mode = 'spectrum'
                else:
                    self.drag_mode = 'rotate'
                    self.camera.is_rotating = False
                self.mouse_x = x
                self.mouse_y = y
            if state == GLUT_UP:
                self.drag_mode = None
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
        if(key == "."):
            self.min_tot += 0.5
            self.reload_blob()
        if(key == ","):
            self.min_tot -= 0.5
            self.reload_blob()
        if(key == 'n'):
            self.load_next_blob()
        if(key == 'p'):
            self.load_previous_blob()
        if(key == 'u'):
            self.toggle_secondaries()
        if(key == 't'):
            self.toggle_spectrum()
        if(key == 'x'):
            self.cmap = self.colourist.next_cmap
        if(key == 'm'):
            self.colourist.print_mode = not self.colourist.print_mode
            self.load_logo()
        if(key == 'a'):
            self.camera.is_rotating = not self.camera.is_rotating
        if(key == 'c'):
            self.colourist.cherenkov_cone_enabled = \
                not self.colourist.cherenkov_cone_enabled
        if(key == "s"):
            event_number = self.blob['start_event'][0]
            try:
                neutrino = self.blob['Neutrino']
            except KeyError:
                neutrino_str = ''
            else:
                neutrino_str = str(neutrino).replace(' ', '_').replace(',', '')
                neutrino_str = neutrino_str.replace('Neutrino:', '')
            screenshot_name = "RA_Event{0}_ToTCut{1}{2}_t{3}ns.png".format(
                        event_number,
                        self.min_tot,
                        neutrino_str,
                        int(self.clock.time)
                    )

            self.save_screenshot(screenshot_name)
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
        if self.drag_mode == 'rotate':
            self.camera.rotate_z(self.mouse_x - x)
            self.camera.move_z(-(self.mouse_y - y)*8)
        if self.drag_mode == 'spectrum':
            self.min_hit_time += (self.mouse_y - y) * 10
            self.max_hit_time += (self.mouse_y - y) * 10
            self.max_hit_time -= (self.mouse_x - x) * 10
            self.min_hit_time += (self.mouse_x - x) * 10
            self.min_hit_time = base_round(self.min_hit_time, 10)
            self.max_hit_time = base_round(self.max_hit_time, 10)
        self.mouse_x = x
        self.mouse_y = y

    def save_screenshot(self, name='screenshot.png'):
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        pixelset = (GLubyte * (3*width*height))(0)
        glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE, pixelset)
        image = Image.frombytes(mode="RGB", size=(width, height), data=pixelset)
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
                'a': 'enable/disable rotation animation',
                'c': 'enable/disable Cherenkov cone',
                't': 'toggle between spectra',
                'u': 'toggle secondaries',
                'x': 'cycle through colour schemes',
                'm': 'toggle screen/print mode',
                's': 'save screenshot (screenshot.png)',
                'v': 'start/stop recording (Frame_XXXXX.jpg)',
                'r': 'reset time',
                '<space>': 'pause time',
                '+ or -': 'zoom in/out',
                ', or .': 'decrease/increase min_tot by 0.5ns',
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
            info_text += "Event #{0}, ToT>{1}ns\n" \
                         .format(event_number, self.min_tot)
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
        draw_text_2d("FPS:  {0:.1f}\nTime: {1:.0f} ns"
                     .format(self.clock.fps, self.clock.time),
                     10, 30)
        draw_text_2d(self.blob_info, 150, 30)


def main():
    from docopt import docopt
    arguments = docopt(__doc__, version=version)
    event_file = arguments['EVENT_FILE']
    detector_file = arguments['-d']
    try:
        min_tot = float(arguments['-t'])
    except TypeError:
        min_tot = 27
    try:
        skip_to_blob = int(arguments['-s'])
    except TypeError:
        skip_to_blob = 0
    app = RainbowAlga(detector_file, event_file, min_tot, skip_to_blob)


if __name__ == "__main__":
    main()
