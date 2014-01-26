# -*- coding: utf-8 -*-
"""
surfer.utils.input
~~~~~~~~~~~~~~~~~~

This module defines the Input class that is responsible for handling
the input coming from the user via the command line.
"""

from surfer.utils import v


class Input:

    def __init__(self):
        self._reset()

    def _reset(self):
        """To reset the input state."""
        self.LEFT = self.RIGHT = self.UP = self.DOWN = None
        self.RETURN = self.ESC = self.TAB = self.CTRL = self.BS = None
        self.INTERRUPT = self.MOUSE = self.MAC_CMD = None
        self.CHAR = ""
        self.F1 = self.F2 = self.F3 = self.F4 = self.F5 = self.F6 = None
        self.F7 = self.F8 = self.F9 = self.F10 = self.F11 = self.F12 = None

    def _nr2char(self, nr):
        return v.call("nr2char({})".format(nr))

    def get(self):
        """To read a key pressed by the user."""
        self._reset()

        try:
            raw_char = v.call('strtrans(getchar())')
        except KeyboardInterrupt:
            # This exception is triggered only on Windows when the user
            # press CTRL+C
            self.CHAR = 'c'
            self.CTRL = True
            self.INTERRUPT = True
            return

        nr = v.call(u"str2nr('{}')".format(raw_char))
        # `nr` == 0 when the user press backspace, an arrow key, F*, etc

        if nr != 0:

            if nr == 13:  # same as Ctrl+m
                self.RETURN = True
            elif nr == 27:
                self.ESC = True
            elif nr == 9:  # same as Ctrl+i
                self.TAB = True
            elif 1 <= nr <= 26:
                self.CTRL = True
                self.CHAR = self._nr2char(nr+96)
                if self.CHAR == 'c':
                    self.INTERRUPT = True
            else:
                self.CHAR = self._nr2char(nr)

        else:

            if 'kl' in raw_char:
                self.LEFT = True
            elif 'kr' in raw_char:
                self.RIGHT = True
            elif 'ku' in raw_char:
                self.UP = True
            elif 'kd' in raw_char:
                self.DOWN = True
            elif 'kb' in raw_char:
                self.BS = True
            elif 'k1' in raw_char:
                self.F1 = True
            elif 'k2' in raw_char:
                self.F2 = True
            elif 'k3' in raw_char:
                self.F3 = True
            elif 'k4' in raw_char:
                self.F4 = True
            elif 'k5' in raw_char:
                self.F5 = True
            elif 'k6' in raw_char:
                self.F6 = True
            elif 'k7' in raw_char:
                self.F7 = True
            elif 'k8' in raw_char:
                self.F8 = True
            elif 'k9' in raw_char:
                self.F9 = True
            elif 'k10' in raw_char:
                self.F10 = True
            elif 'k11' in raw_char:
                self.F11 = True
            elif 'k12' in raw_char:
                self.F12 = True
            else:
                # mouse clicks or scrolls
                self.MOUSE = True

