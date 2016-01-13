from __future__ import division, absolute_import, print_function

class Position(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class Alga(object):
    def setup(self, event):
        pass

    def draw(self, time):
        """Draw objects within a 3D context"""
        pass

    def draw_shaded(self, time):
        """Draw objects within a shaded 3D context"""
        pass

    def draw2d(self, time):
        """Draw objects within a 2D context"""
        pass
