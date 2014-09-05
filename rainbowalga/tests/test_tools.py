from __future__ import division, absolute_import, print_function

import unittest
from time import sleep

from rainbowalga.tools import Clock


class TestClock(unittest.TestCase):

    def test_init(self):
        clock = Clock()

    def test_time(self):
        clock = Clock()
        sleep(0.1)
        self.assertAlmostEqual(0.1, clock.time, 2)

    def test_speed(self):
        clock = Clock(speed=2)
        sleep(0.1)
        self.assertAlmostEqual(0.2, clock.time, 2)

    def test_reset(self):
        clock = Clock()
        sleep(0.1)
        clock.reset()
        self.assertAlmostEqual(0, clock.time, 2)

    def test_pause_is_paused(self):
        clock = Clock()
        clock.pause()
        self.assertTrue(clock.is_paused)

    def test_resume_resumes(self):
        clock = Clock()
        clock.pause()
        clock.resume()
        self.assertFalse(clock.is_paused)

    def test_clock_returns_correct_time_after_pause(self):
        clock = Clock()
        sleep(0.1)
        clock.pause()
        sleep(0.1)
        clock.resume()
        sleep(0.1)
        self.assertAlmostEqual(0.2, clock.time, 2)

    def test_snooze(self):
        clock = Clock(snooze_interval=0.2)
        clock.snooze()
        sleep(0.1)
        self.assertTrue(clock.is_snoozed)
        sleep(0.11)
        self.assertFalse(clock.is_snoozed)

    def test_fps(self):
        clock = Clock()
        for frame in xrange(5):
            clock.record_frame_time()
            sleep(0.1)
        self.assertAlmostEqual(10, clock.fps, 0)

    def test_fps_returns_zero_if_no_frame_recorded(self):
        clock = Clock()
        self.assertEqual(0, clock.fps)

    def test_fps_returns_zero_if_only_one_frame_recorded(self):
        clock = Clock()
        clock.record_frame_time
        self.assertEqual(0, clock.fps)


if __name__ == '__main__':
    unittest.main()
