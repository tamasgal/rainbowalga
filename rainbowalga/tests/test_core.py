from __future__ import division, absolute_import, print_function

import unittest

from rainbowalga.core import Position


class TestPosition(unittest.TestCase):

    def test_x_y_z(self):
        position = Position(1, 2, 3)
        self.assertEqual(1, position.x)
        self.assertEqual(2, position.y)
        self.assertEqual(3, position.z)


if __name__ == '__main__':
    unittest.main()
