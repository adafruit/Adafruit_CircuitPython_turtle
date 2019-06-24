# Based on turtle.py, a Tkinter based turtle graphics module for Python
# Version 1.1b - 4. 5. 2009
# Copyright (C) 2006 - 2010  Gregor Lingl
# email: glingl@aon.at
#
# The MIT License (MIT)
#
# Copyright (c) 2019 LadyAda and Dave Astels for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_turtle`
================================================================================

Turtle graphics library for CircuitPython and displayio


* Author(s): LadyAda and Dave Astels

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s). Use unordered list & hyperlink rST
   inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import displayio
import board
import gc
import math
import time
import adafruit_logging as logging

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_turtle.git"

class Color:
    WHITE = 0xFFFFFF
    BLACK = 0x0000
    RED =  0xFF0000
    ORANGE = 0xFFA500
    YELLOW = 0xFFFF00
    GREEN =  0x00FF00
    BLUE = 0x0000FF
    PURPLE = 0x800080
    PINK = 0xFFC0CB

    colors = (WHITE, BLACK, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK)

class Vec2D(tuple):
    """A 2 dimensional vector class, used as a helper class
    for implementing turtle graphics.
    May be useful for turtle graphics programs also.
    Derived from tuple, so a vector is a tuple!
    Provides (for a, b vectors, k number):
       a+b vector addition
       a-b vector subtraction
       a*b inner product
       k*a and a*k multiplication with scalar
       |a| absolute value of a
       a.rotate(angle) rotation
    """
    def __init__(cls, x, y):
        super().__init__((x, y))

    def __add__(self, other):
        return Vec2D(self[0] + other[0], self[1] + other[1])

    def __mul__(self, other):
        if isinstance(other, Vec2D):
            return self[0] * other[0]+self[1] * other[1]
        return Vec2D(self[0] * other, self[1] * other)

    def __rmul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vec2D(self[0] * other, self[1] * other)

    def __sub__(self, other):
        return Vec2D(self[0] - other[0], self[1] - other[1])

    def __neg__(self):
        return Vec2D(-self[0], -self[1])

    def __abs__(self):
        return (self[0]**2 + self[1]**2)**0.5

    def rotate(self, angle):
        """rotate self counterclockwise by angle
        """
        perp = Vec2D(-self[1], self[0])
        angle = angle * math.pi / 180.0
        c, s = math.cos(angle), math.sin(angle)
        return Vec2D(self[0] * c + perp[0] * s, self[1] * c + perp[1] * s)

    def __getnewargs__(self):
        return (self[0], self[1])

    def __repr__(self):
        return "(%.2f,%.2f)" % self


class turtle:

    def __init__(self, display=board.DISPLAY):
        self._logger = logging.getLogger("Turtle")
        self._logger.setLevel(logging.DEBUG)
        self._display = display
        self._w = self._display.width
        self._h = self._display.height
        self._x = self._w // 2
        self._y = self._h // 2
        self._speed = 6
        self._heading = 90
        self._logomode = False

        self._splash = displayio.Group(max_size=3)

        self._bg_bitmap = displayio.Bitmap(self._w, self._h, 1)
        self._bg_palette = displayio.Palette(1)
        self._bg_palette[0] = Color.BLACK
        self._bg_sprite = displayio.TileGrid(self._bg_bitmap,
                                            pixel_shader=self._bg_palette,
                                            x=0, y=0)
        self._splash.append(self._bg_sprite)

        self._fg_bitmap = displayio.Bitmap(self._w, self._h, 5)
        self._fg_palette = displayio.Palette(len(Color.colors) + 1)
        self._fg_palette.make_transparent(0)
        for i,c in enumerate(Color.colors):
            self._fg_palette[i + 1] = c
        self._fg_sprite = displayio.TileGrid(self._fg_bitmap,
                                            pixel_shader=self._fg_palette,
                                            x=0, y=0)
        self._splash.append(self._fg_sprite)

        self._turtle_bitmap = displayio.Bitmap(9, 9, 2)
        self._turtle_palette = displayio.Palette(2)
        self._turtle_palette.make_transparent(0)
        self._turtle_palette[1] = Color.WHITE
        for i in range(4):
            self._turtle_bitmap[4 - i, i] = 1
            self._turtle_bitmap[i, 4 + i] = 1
            self._turtle_bitmap[4 + i, 7 - i] = 1
            self._turtle_bitmap[4 + i, i] = 1
        self._turtle_sprite = displayio.TileGrid(self._turtle_bitmap,
                                            pixel_shader=self._turtle_palette,
                                            x=-100, y=-100)
        self._drawturtle()
        self._splash.append(self._turtle_sprite)

        self._penstate = False
        self._pencolor = None
        self.pencolor(Color.WHITE)

        self._display.show(self._splash)
        self._display.refresh_soon()
        gc.collect()
        self._display.wait_for_frame()

    def _drawturtle(self):
        self._turtle_sprite.x = int(self._x - 4)
        self._turtle_sprite.y = int(self._y - 4)
        #self._logger.debug("pos (%d, %d)", self._x, self._y)

    # Turtle motion
    def forward(self, distance):
        p = self.pos()
        x1 = p[0] + math.sin(math.radians(self._heading)) * distance
        y1 = p[1] + math.cos(math.radians(self._heading)) * distance
        self.goto(x1, y1)
    fd = forward

    def backward(self, distance):
        self.forward(-distance)
    bk = backward
    back = backward

    def right(self, angle):
        self._turn(angle)
    rt = right

    def left(self, angle):
        self._turn(-angle)
    lt = left

    def goto(self, x1, y1=None):
        if y1 is None:
            y1 = x1[1]
            x1 = x1[0]
        x1 += self._w // 2
        y1 = self._h // 2 - y1
        x0 = self._x
        y0 = self._y
        self._logger.debug("* GoTo from (%d, %d) to (%d, %d)", x0, y0, x1, y1)
        if not self.isdown():
            self._x = x1    # woot, we just skip ahead
            self._y = y1
            self._drawturtle()
            return
        steep = abs(y1 - y0) > abs(x1 - x0)
        rev = False
        dx = x1 - x0

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
            dx = x1 - x0

        if x0 > x1:
            rev = True
            dx = x0 - x1

        dy = abs(y1 - y0)
        err = dx / 2
        ystep = -1
        if y0 < y1:
            ystep = 1

        while (not rev and x0 <= x1) or (rev and x1 <= x0):
            if steep:
                try:
                    self._fg_bitmap[int(y0), int(x0)] = self._pencolor
                except IndexError:
                    pass
                self._x = y0
                self._y = x0
                self._drawturtle()
                time.sleep(0.003)
            else:
                try:
                    self._fg_bitmap[int(x0), int(y0)] = self._pencolor
                except IndexError:
                    pass
                self._x = x0
                self._y = y0
                self._drawturtle()
                time.sleep(0.003)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            if rev:
                x0 -= 1
            else:
                x0 += 1
    setpos = goto
    setposition = goto

    def setx(self, x):
        self.goto(x, self.pos()[1])

    def sety(self, y):
        self.goto(self.pos()[0], y)

    def setheading(self, to_angle):
        self._heading = to_angle
    seth = setheading

    def home(self):
        self.setheading(90)
        self.goto(0,0)

    def circle(self, radius, extent=None, steps=None):
        raise NotImplementedError

    def dot(self, size=None, *color):
        raise NotImplementedError

    def stamp(self):
        raise NotImplementedError

    def clearstamp(self):
        raise NotImplementedError

    def clearstamps(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def speed(self, speed=None):
        raise NotImplementedError


    ####################
    # Tell turtle's state
    def pos(self):
        return Vec2D(self._x - self._w // 2, self._h // 2 - self._y)
    position=pos

    def clear(self):
        for w in range(self._w):
            for h in range(self._h):
                self._fg_bitmap[w, h] = 0
        for i, c in enumerate(Color.colors):
            self._fg_palette[i + 1] = c ^ 0xFFFFFF
        self._display.refresh_soon()
        for i, c in enumerate(Color.colors):
            self._fg_palette[i + 1] = c
        self._display.refresh_soon()
        time.sleep(0.1)

    def heading(self):
        return self._heading

    # Pen control
    def pendown(self):
        self._penstate = True
    pd = pendown
    down = pendown

    def penup(self):
        self._penstate = False
    pu = penup
    up = penup

    def isdown(self):
        return self._penstate

    def pencolor(self, c):
        if not c in Color.colors:
            raise RuntimeError("Color must be one of the 'color' class items")
        self._pencolor = 1 + Color.colors.index(c)

    def mode(self, mode=None):
        if mode == "standard":
            self._logomode = False
        elif mode == "logo":
            self._logomode = True
        elif mode is None:
            if self._logomode:
                return "logo"
            else:
                return "standard"
        else:
            raise RuntimeError("Mode must be 'logo' or 'standard!'")

    def _turn(self, angle):
        if self._logomode:
            self._heading -= angle
        else:
            self._heading += angle
        self._heading %= 360         # wrap around
