# coding=utf-8
# Filename: gui.py
"""
RainbowAlga GUI stuff.

"""
from __future__ import division, absolute_import, print_function

from OpenGL.GL import glColor3f, glClearColor


class Colourist(object):
    """Takes care of the colours in OpenGL"""
    def __init__(self):
        self.print_mode = False 
        pass

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
