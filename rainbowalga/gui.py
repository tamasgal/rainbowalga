# coding=utf-8
# Filename: gui.py
"""
RainbowAlga GUI stuff.

"""
from __future__ import division, absolute_import, print_function

from OpenGL.GL import glColor3f, glClearColor

import pylab
import itertools

from km3pipe.logger import logging
log = logging.getLogger('rainbowalga')  # pylint: disable=C0103

class Colourist(object):
    """Takes care of the colours in OpenGL. (Singleton)"""
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Colourist, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        log.info("Initialising colourist.")
        self.print_mode = False
        self.cherenkov_cone_enabled = False
        self.cmap_names = ['RdBu', 'seismic', 'Set1', 'brg', 'gist_rainbow']
        self.cmap_generator = itertools.cycle(self.cmap_names)
        pass

    @property
    def default_cmap(self):
        return pylab.get_cmap(self.cmap_names[-1])

    @property
    def next_cmap(self):
        return pylab.get_cmap(next(self.cmap_generator))

    def now_text(self):
        if self.print_mode:
            glColor3f(0.1, 0.1, 0.1)
        else:
            glColor3f(1.0, 1.0, 1.0)

    def now_background(self):
        if self.print_mode:
            glClearColor(1.0, 1.0, 1.0, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)

    def now_detector_lines(self):
        if self.print_mode:
            glClearColor(0.0, 0.0, 0.0, 1.0)
        else:
            glClearColor(1.0, 1.0, 1.0, 1.0)
