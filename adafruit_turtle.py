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

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

#pylint:disable=too-many-public-methods, too-many-instance-attributes, invalid-name
#pylint:disable=too-few-public-methods, too-many-lines, too-many-arguments

import gc
import math
import time
import board
import displayio
import adafruit_logging as logging

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_turtle.git"

class Color(object):
    """Standard colors"""
    WHITE = 0xFFFFFF
    BLACK = 0x000000
    RED = 0xFF0000
    ORANGE = 0xFFA500
    YELLOW = 0xFFFF00
    GREEN = 0x00FF00
    BLUE = 0x0000FF
    PURPLE = 0x800080
    PINK = 0xFFC0CB

    colors = (WHITE, BLACK, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK)

    def __init__(self):
        pass


class Vec2D(tuple):
    """A 2 dimensional vector class, used as a helper class
    for implementing turtle graphics.
    May be useful for turtle graphics programs also.
    Derived from tuple, so a vector is a tuple!
    """
    # Provides (for a, b vectors, k number):
    #     a+b vector addition
    #     a-b vector subtraction
    #     a*b inner product
    #     k*a and a*k multiplication with scalar
    #     |a| absolute value of a
    #     a.rotate(angle) rotation
    def __init__(self, x, y):
        super(Vec2D, self).__init__((x, y))

    def __add__(self, other):
        return Vec2D(self[0] + other[0], self[1] + other[1])

    def __mul__(self, other):
        if isinstance(other, Vec2D):
            return self[0] * other[0]+self[1] * other[1]
        return Vec2D(self[0] * other, self[1] * other)

    def __rmul__(self, other):
        if isinstance(other, (float, int)):
            return Vec2D(self[0] * other, self[1] * other)
        return None

    def __sub__(self, other):
        return Vec2D(self[0] - other[0], self[1] - other[1])

    def __neg__(self):
        return Vec2D(-self[0], -self[1])

    def __abs__(self):
        return (self[0]**2 + self[1]**2)**0.5

    def rotate(self, angle):
        """Rotate self counterclockwise by angle.

        :param angle: how much to rotate

        """
        perp = Vec2D(-self[1], self[0])
        angle = angle * math.pi / 180.0
        c, s = math.cos(angle), math.sin(angle)
        return Vec2D(self[0] * c + perp[0] * s, self[1] * c + perp[1] * s)

    def __getnewargs__(self):
        return (self[0], self[1])

    def __repr__(self):
        return "({:.2f},{:.2f})".format(self[0], self[1])

class turtle(object):
    """A Turtle that can be given commands to draw."""

    def __init__(self, display=None):
        if display:
            self._display = display
        else:
            try:
                self._display = board.DISPLAY
            except AttributeError:
                raise RuntimeError("No display available. One must be provided.")
        self._logger = logging.getLogger("Turtle")
        self._logger.setLevel(logging.INFO)
        self._w = self._display.width
        self._h = self._display.height
        self._x = self._w // 2
        self._y = self._h // 2
        self._speed = 6
        self._heading = 90
        self._logomode = False
        self._fullcircle = 360.0
        self._degreesPerAU = 1.0
        self._mode = "standard"
        self._angleOffset = 0

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
        for i, c in enumerate(Color.colors):
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
        self._pensize = 1
        self.pencolor(Color.WHITE)

        self._display.show(self._splash)
        gc.collect()

    def _drawturtle(self):
        self._turtle_sprite.x = int(self._x - 4)
        self._turtle_sprite.y = int(self._y - 4)
        #self._logger.debug("pos (%d, %d)", self._x, self._y)

    ############################################################################
    # Move and draw

    def forward(self, distance):
        """Move the turtle forward by the specified distance, in the direction the turtle is headed.

        :param distance: how far to move (integer or float)
        """
        p = self.pos()
        x1 = p[0] + math.sin(math.radians(self._heading)) * distance
        y1 = p[1] + math.cos(math.radians(self._heading)) * distance
        self.goto(x1, y1)
    fd = forward

    def backward(self, distance):
        """Move the turtle backward by distance, opposite to the direction the turtle is headed.
        Does not change the turtle's heading.

        :param distance: how far to move (integer or float)
        """

        self.forward(-distance)
    bk = backward
    back = backward

    def right(self, angle):
        """Turn turtle right by angle units. (Units are by default degrees,
        but can be set via the degrees() and radians() functions.)
        Angle orientation depends on the turtle mode, see mode().

        :param angle: how much to rotate to the right (integer or float)
        """
        self._turn(angle)
    rt = right

    def left(self, angle):
        """Turn turtle left by angle units. (Units are by default degrees,
        but can be set via the degrees() and radians() functions.)
        Angle orientation depends on the turtle mode, see mode().

        :param angle: how much to rotate to the left (integer or float)
        """
        self._turn(-angle)
    lt = left

    #pylint:disable=too-many-branches,too-many-statements
    def goto(self, x1, y1=None):
        """If y1 is None, x1 must be a pair of coordinates or an (x, y) tuple

        Move turtle to an absolute position. If the pen is down, draw line.
        Does not change the turtle's orientation.

        :param x1: a number or a pair of numbers
        :param y1: a number or None
        """
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
                    self._plot(int(y0), int(x0), self._pencolor)
                except IndexError:
                    pass
                self._x = y0
                self._y = x0
                self._drawturtle()
            else:
                try:
                    self._plot(int(x0), int(y0), self._pencolor)
                except IndexError:
                    pass
                self._x = x0
                self._y = y0
                self._drawturtle()
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
        """Set the turtle's first coordinate to x, leave second coordinate
        unchanged.

        :param x: new value of the turtle's x coordinate (a number)

        """
        self.goto(x, self.pos()[1])

    def sety(self, y):
        """Set the turtle's second coordinate to y, leave first coordinate
        unchanged.

        :param y: new value of the turtle's y coordinate (a number)

        """
        self.goto(self.pos()[0], y)

    def setheading(self, to_angle):
        """Set the orientation of the turtle to to_angle. Here are some common
        directions in degrees:

        standard mode | logo mode
        0 - east | 0 - north
        90 - north | 90 - east
        180 - west | 180 - south
        270 - south | 270 - west

        :param to_angle: the new turtle heading

        """

        self._heading = to_angle
    seth = setheading

    def home(self):
        """Move turtle to the origin - coordinates (0,0) - and set its heading to
        its start-orientation
        (which depends on the mode, see mode()).
        """
        self.setheading(90)
        self.goto(0, 0)

    def _plot(self, x, y, c):
        try:
            self._fg_bitmap[int(x), int(y)] = c
        except IndexError:
            pass

    def circle(self, radius, extent=None, steps=None):
        """Draw a circle with given radius. The center is radius units left of
        the turtle; extent - an angle - determines which part of the circle is
        drawn. If extent is not given, draw the entire circle. If extent is not
        a full circle, one endpoint of the arc is the current pen position.
        Draw the arc in counterclockwise direction if radius is positive,
        otherwise in clockwise direction. Finally the direction of the turtle
        is changed by the amount of extent.

        As the circle is approximated by an inscribed regular polygon, steps
        determines the number of steps to use. If not given, it will be
        calculated automatically. May be used to draw regular polygons.

        :param radius: the radius of the circle
        :param extent: the arc of the circle to be drawn
        :param steps: how many points along the arc are computed
        """
        # call: circle(radius)                  # full circle
        # --or: circle(radius, extent)          # arc
        # --or: circle(radius, extent, steps)
        # --or: circle(radius, steps=6)         # 6-sided polygon

        if extent is None:
            extent = self._fullcircle
        if steps is None:
            frac = abs(extent)/self._fullcircle
            steps = 1+int(min(11+abs(radius)/6.0, 59.0)*frac)
        w = 1.0 * extent / steps
        w2 = 0.5 * w
        l = 2.0 * radius * math.sin(w2*math.pi/180.0*self._degreesPerAU)
        if radius < 0:
            l, w, w2 = -l, -w, -w2
        self.left(w2)
        for _ in range(steps):
            self.forward(l)
            self.left(w)
        self.right(w2)

    def _draw_disk(self, x, y, width, height, r, color, fill=True, outline=True, stroke=1):
        """Draw a filled and/or outlined circle"""
        if fill:
            self._helper(x+r, y+r, r, color=color, fill=True,
                         x_offset=width-2*r-1, y_offset=height-2*r-1)
        if outline:
            self._helper(x+r, y+r, r, color=color, stroke=stroke,
                         x_offset=width-2*r-1, y_offset=height-2*r-1)

  # pylint: disable=too-many-locals, too-many-branches
    def _helper(self, x0, y0, r, color, x_offset=0, y_offset=0,
                stroke=1, fill=False):
        """Draw quandrant wedges filled or outlined"""
        f = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x = -1
        y = r

        while x < y:
            if f >= 0:
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x
            if fill:
                for w in range(x0-y, x0+y+x_offset):
                    self._plot(w, y0 + x + y_offset, color)
                    self._plot(w, y0 - x, color)
                for w in range(x0-x, x0+x+x_offset):
                    self._plot(w, y0 + y + y_offset, color)
                    self._plot(w, y0 - y, color)
            else:
                for line in range(stroke):
                    self._plot(x0 - y + line, y0 + x + y_offset, color)
                    self._plot(x0 - x, y0 + y + y_offset - line, color)
                    self._plot(x0 - y + line, y0 - x, color)
                    self._plot(x0 - x, y0 - y + line, color)
            for line in range(stroke):
                self._plot(x0 + x + x_offset, y0 + y + y_offset - line, color)
                self._plot(x0 + y + x_offset - line, y0 + x + y_offset, color)
                self._plot(x0 + x + x_offset, y0 - y + line, color)
                self._plot(x0 + y + x_offset - line, y0 - x, color)

    # pylint: enable=too-many-locals, too-many-branches

#pylint:disable=keyword-arg-before-vararg
    def dot(self, size=None, color=None):
        """Draw a circular dot with diameter size, using color.
        If size is not given, the maximum of pensize+4 and
        2*pensize is used.

        :param size: the diameter of the dot
        :param color: the color of the dot

        """
        if size is None:
            size = max(self._pensize + 4, self._pensize * 2)
        if color is None:
            color = self._pencolor
        else:
            color = self._color_to_pencolor(color)
        self._logger.debug('dot(%d)', size)
        self._draw_disk(self._x - size, self._y - size, 2 * size + 1, 2 * size + 1, size, color)
        self._fg_sprite[0, 0] = 0

    def stamp(self):
        """Not implemented

        Stamp a copy of the turtle shape onto the canvas at the current
        turtle position. Return a stamp_id for that stamp, which can be used to
        delete it by calling clearstamp(stamp_id).
        """
        raise NotImplementedError

    def clearstamp(self, stampid):
        """Not implemented

        Delete stamp with given stampid.

        :param stampid: the id of the stamp to be deleted

        """
        raise NotImplementedError

    def clearstamps(self, n=None):
        """Not implemented

        Delete all or first/last n of turtle's stamps. If n is None, delete
        all stamps, if n > 0 delete first n stamps, else if n < 0 delete last
        n stamps.

        :param n: how many stamps to delete (None means delete them all)

        """
        raise NotImplementedError

    def undo(self):
        """Not implemented

        Undo (repeatedly) the last turtle action(s). Number of available undo
        actions is determined by the size of the undobuffer.
        """
        raise NotImplementedError

    def speed(self, speed=None):
        """Not implemented

        Set the turtle's speed to an integer value in the range 0..10. If no
        argument is given, return current speed.

        If input is a number greater than 10 or smaller than 0.5, speed is set
        to 0. Speedstrings are mapped to speedvalues as follows:

        "fastest": 0
        "fast": 10
        "normal": 6
        "slow": 3
        "slowest": 1
        Speeds from 1 to 10 enforce increasingly faster animation of line
        drawing and turtle turning.

        Attention: speed = 0 means that no animation takes place.
        forward/back makes turtle jump and likewise left/right make the
        turtle turn instantly.

        :param speed: the new turtle speed (0..10) or None
        """
        raise NotImplementedError


    ############################################################################
    # Tell turtle's state

    def pos(self):
        """Return the turtle's current location (x,y) (as a Vec2D vector)."""
        return Vec2D(self._x - self._w // 2, self._h // 2 - self._y)
    position = pos

    def towards(self, x1, y1=None):
        """Not implemented

        Return the angle between the line from turtle position to position
        specified by (x,y) or the vector. This depends on the turtle's start
        orientation which depends on the mode - "standard" or "logo").

        :param x: a number or a pair/vector of numbers
        :param y: a number if x is a number, else None

        """
        raise NotImplementedError

    def xcor(self):
        """Return the turtle's x coordinate."""
        return self._x - self._w // 2

    def ycor(self):
        """Return the turtle's y coordinate."""
        return self._h // 2 - self._y

    def heading(self):
        """Return the turtle's current heading (value depends on the turtle
        mode, see mode()).
        """
        return self._heading

    def distance(self, x1, y1=None):
        """Not implemented

        Return the distance from the turtle to (x,y) or the vector, in turtle
        step units.

        :param x: a number or a pair/vector of numbers
        :param y: a number if x is a number, else None

        """
        raise NotImplementedError

    ############################################################################
    # Setting and measurement

    def _setDegreesPerAU(self, fullcircle):
        """Helper function for degrees() and radians()"""
        self._fullcircle = fullcircle
        self._degreesPerAU = 360/fullcircle
        if self._mode == "standard":
            self._angleOffset = 0
        else:
            self._angleOffset = fullcircle/4.


    def degrees(self, fullcircle=360):
        """Set angle measurement units, i.e. set number of "degrees" for a full circle.
        Default value is 360 degrees.

        :param fullcircle: the number of degrees in a full circle
        """
        self._setDegreesPerAU(fullcircle)

    def radians(self):
        """Set the angle measurement units to radians. Equivalent to degrees(2*math.pi)."""
        self._setDegreesPerAU(2*math.pi)


    ############################################################################
    # Drawing state

    def pendown(self):
        """Pull the pen down - drawing when moving."""
        self._penstate = True
    pd = pendown
    down = pendown

    def penup(self):
        """Pull the pen up - no drawing when moving."""
        self._penstate = False
    pu = penup
    up = penup

    def pensize(self, width=None):
        """Not implemented

        Set the line thickness to width or return it. If resizemode is set to
        "auto" and turtleshape is a polygon, that polygon is drawn with the same
        line thickness. If no argument is given, the current pensize is returned.

        :param width: - a positive number

        """
        if width is not None:
            self._pensize = width
        return self._pensize
    width = pensize

    def pen(self, pen=None, **pendict):
        """Not implemented

        Not implemented

        Return or set the pen's attributes in a "pen-dictionary" with
        the following key/value pairs:

        "shown": True/False
        "pendown": True/False
        "pencolor": color-string or color-tuple
        "fillcolor": color-string or color-tuple
        "pensize": positive number
        "speed": number in range 0..10
        "resizemode": "auto" or "user" or "noresize"
        "stretchfactor": (positive number, positive number)
        "outline": positive number
        "tilt": number

        This dictionary can be used as argument for a subsequent call to pen()
        to restore the former pen-state. Moreover one or more of these
        attributes can be provided as keyword-arguments. This can be used to
        set several pen attributes in one statement.

        :param pen: a dictionary with some or all of the above listed keys
        :param pendict: ne or more keyword-arguments with the above listed keys
                        as keywords
        """

        raise NotImplementedError

    def isdown(self):
        """Return True if pen is down, False if it's up."""
        return self._penstate

    ############################################################################
    # Color control

#pylint:disable=no-self-use
    def _color_to_pencolor(self, c):
        return 1 + Color.colors.index(c)
#pylint:enable=no-self-use

    def color(self, *args):
        """Not implemented

        Return or set pencolor and fillcolor.

        Several input formats are allowed. They use 0 to 3 arguments as follows:

        color()
            Return the current pencolor and the current fillcolor as a pair of
            color specification strings or tuples as returned by pencolor() and
            fillcolor().

        color(colorstring), color((r, g, b)), color(r, g, b)
            Inputs as in pencolor(), set both, fillcolor and pencolor, to the
            given value.

        color(colorstring1, colorstring2), color((r1, g1, b1), (r2, g2, b2))
            Equivalent to pencolor(colorstring1) and fillcolor(colorstring2)
            and analogously if the other input format is used.

        If turtleshape is a polygon, outline and interior of that polygon is
        drawn with the newly set colors.
        """
        raise NotImplementedError

    def pencolor(self, c=None):
        """
        Return or set the pencolor.

        Four input formats are allowed:

        pencolor()
            Return the current pencolor as color specification string or as a
            tuple (see example). May be used as input to another color/
            pencolor/fillcolor call.

        pencolor(colorvalue)
            Set pencolor to colorvalue, which is a 24-bit integer such as 0xFF0000.
            The Color class provides the available values:
            WHITE, BLACK, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK

        If turtleshape is a polygon, the outline of that polygon is drawn with
        the newly set pencolor.
        """
        if c is None:
            return Color.colors[self._pencolor - 1]
        if not c in Color.colors:
            raise RuntimeError("Color must be one of the 'Color' class items")
        self._pencolor = 1 + Color.colors.index(c)
        return c

    def fillcolor(self, c=None):
        """Not implemented

        Return or set the fillcolor.

        Four input formats are allowed:

        fillcolor()
            Return the current fillcolor as color specification string, possibly
            in tuple format (see example). May be used as input to another
            color/pencolor/fillcolor call.

        fillcolor(colorstring)
            Set fillcolor to colorstring, which is a Tk color specification
            string, such as "red", "yellow", or "#33cc8c".

        fillcolor((r, g, b))
            Set fillcolor to the RGB color represented by the tuple of r, g, and
            b. Each of r, g, and b must be in the range 0..colormode, where
            colormode is either 1.0 or 255 (see colormode()).

        fillcolor(r, g, b)
            Set fillcolor to the RGB color represented by r, g, and b. Each of
            r, g, and b must be in the range 0..colormode.

        If turtleshape is a polygon, the interior of that polygon is drawn with
        the newly set fillcolor.
        """
        raise NotImplementedError

    ############################################################################
    # Filling

    def filling(self):
        """Not implemented

        Return fillstate (True if filling, False else)."""
        raise NotImplementedError

    def begin_fill(self):
        """Not implemented

        To be called just before drawing a shape to be filled."""
        raise NotImplementedError

    def end_fill(self):
        """Not implemented

        Fill the shape drawn after the last call to begin_fill()."""
        raise NotImplementedError

    ############################################################################
    # More drawing control

    def reset(self):
        """Not implemented

        Delete the turtle's drawings from the screen, re-center the turtle
        and set variables to the default values."""
        raise NotImplementedError

    def clear(self):
        """Delete the turtle's drawings from the screen. Do not move turtle."""
        for w in range(self._w):
            for h in range(self._h):
                self._fg_bitmap[w, h] = 0
        for i, c in enumerate(Color.colors):
            self._fg_palette[i + 1] = c ^ 0xFFFFFF
        for i, c in enumerate(Color.colors):
            self._fg_palette[i + 1] = c
        time.sleep(0.1)

    def write(self, arg, move=False, align="left", font=("Arial", 8, "normal")):
        """Not implemented

        Write text - the string representation of arg - at the current turtle
        position according to align ("left", "center" or "right") and with the
        given font. If move is true, the pen is moved to the bottom-right corner
        of the text. By default, move is False.

        :param arg: object to be written to the TurtleScreen
        :param move": True/False
        :param align: one of the strings "left", "center" or "right"
        :param font: a triple (fontname, fontsize, fonttype)

        """
        raise NotImplementedError

    ############################################################################
    # Visibility

    def showturtle(self):
        """Not implemented

        Make the turtle visible."""
        raise NotImplementedError
    st = showturtle

    def hideturtle(self):
        """Not implemented

        Make the turtle invisible."""
        raise NotImplementedError
    ht = hideturtle

    def isvisible(self):
        """Not implemented

        Return True if the Turtle is shown, False if it's hidden."""
        raise NotImplementedError

    ############################################################################
    # Appearance

    def shape(self, name=None):
        """Not implemented

        Set turtle shape to shape with given name or, if name is not
        given, return name of current shape. Shape with name must exist
        in the TurtleScreen's shape dictionary. Initially there are the
        following polygon shapes: "arrow", "turtle", "circle", "square",
        "triangle", "classic". To learn about how to deal with shapes
        see Screen method register_shape().

        :param name: a string which is a valid shapename

        """
        raise NotImplementedError

    def resizemode(self, rmode=None):
        """Not implemented

        Set resizemode to one of the values: "auto", "user",

        "noresize". If rmode is not given, return current
        resizemode. Different resizemodes have the following effects:

        "auto": adapts the appearance of the turtle corresponding to the value
        of pensize.

        "user": adapts the appearance of the turtle according to the values of
        stretchfactor and outlinewidth (outline), which are set by shapesize().

        "noresize": no adaption of the turtle's appearance takes place.

        resizemode("user") is called by shapesize() when used with arguments.

        :param rmode: one of the strings "auto", "user", or "noresize"

        """
        raise NotImplementedError

    def shapesize(self, stretch_wid=None, stretch_len=None, outline=None):
        """Not implemented

        Return or set the pen's attributes x/y-stretchfactors and/or
        outline. Set resizemode to "user". If and only if resizemode is
        set to "user", the turtle will be displayed stretched according
        to its stretchfactors: stretch_wid is stretchfactor
        perpendicular to its orientation, stretch_len is stretchfactor
        in direction of its orientation, outline determines the width of
        the shapes's outline.

        :param stretch_wid: positive number
        :param stretch_len: positive number
        :param outline: positive number

        """
        raise NotImplementedError
    turtlesize = shapesize

    def sheerfactor(self, shear=None):
        """Not implemented

        Set or return the current shearfactor. Shear the turtleshape
        according to the given shearfactor shear, which is the tangent
        of the shear angle. Do not change the turtle's heading
        (direction of movement). If shear is not given: return the
        current shearfactor, i. e. the tangent of the shear angle, by
        which lines parallel to the heading of the turtle are sheared.

        :param shear: number (optional)

        """
        raise NotImplementedError

    def settiltangle(self, angle):
        """Not implemented

        Rotate the turtleshape to point in the direction specified by
        angle, regardless of its current tilt-angle. Do not change the
        turtle's heading (direction of movement).

        :param angle: a number

        """
        raise NotImplementedError

    def tiltangle(self, angle=None):
        """Not implemented

        Set or return the current tilt-angle. If angle is given,
        rotate the turtleshape to point in the direction specified by
        angle, regardless of its current tilt-angle. Do not change the
        turtle's heading (direction of movement). If angle is not given:
        return the current tilt-angle, i. e. the angle between the
        orientation of the turtleshape and the heading of the turtle
        (its direction of movement).

        :param angle: a number (optional)

        """
        raise NotImplementedError

    def tilt(self, angle):
        """Not implemented

        Rotate the turtleshape by angle from its current tilt-angle,
        but do not change the turtle's heading (direction of movement).

        :param angle: a number
        """
        raise NotImplementedError

    def shapetransform(self, t11=None, t12=None, t21=None, t22=None):
        """Not implemented

        Set or return the current transformation matrix of the turtle shape.

        If none of the matrix elements are given, return the transformation
        matrix as a tuple of 4 elements. Otherwise set the given elements and
        transform the turtleshape according to the matrix consisting of first
        row t11, t12 and second row t21, 22. The determinant t11 * t22 - t12 *
        t21 must not be zero, otherwise an error is raised. Modify
        stretchfactor, shearfactor and tiltangle according to the given matrix.

        :param t11: a number (optional)
        :param t12: a number (optional)
        :param t21: a number (optional)
        :param t12: a number (optional)

        """
        raise NotImplementedError

    def get_shapepoly(self):
        """Not implemented

        Return the current shape polygon as tuple of coordinate
        pairs. This can be used to define a new shape or components of a
        compound shape.
        """
        raise NotImplementedError

    ############################################################################
    # Using events

    def onclick(self, fun, btn=1, add=None):
        """Not implemented

        Bind fun to mouse-click events on this turtle. If fun is

        None, existing bindings are removed.

        :param fun: a function with two arguments which will be called with the
                    coordinates of the clicked point on the canvas

        :param btn: number of the mouse-button, defaults to 1 (left mouse button)

        :param add: True or False - if True, a new binding will be added,
                    otherwise it will replace a former binding

        """
        raise NotImplementedError

    def onrelease(self, fun, btn=1, add=None):
        """Not implemented

        Bind fun to mouse-button-release events on this turtle. If
        fun is None, existing bindings are removed.

        :param fun: a function with two arguments which will be called with the
                    coordinates of the clicked point on the canvas

        :param btn: number of the mouse-button, defaults to 1 (left mouse button)

        :param add: True or False - if True, a new binding will be added,
                    otherwise it will replace a former binding

        """
        raise NotImplementedError

    def ondrag(self, fun, btn=1, add=None):
        """Not implemented

        Bind fun to mouse-move events on this turtle. If fun is None,
        existing bindings are removed.

        Remark: Every sequence of mouse-move-events on a turtle is
        preceded by a mouse-click event on that turtle.

        :param fun: a function with two arguments which will be called with the
                    coordinates of the clicked point on the canvas

        :param btn: number of the mouse-button, defaults to 1 (left mouse button)

        :param add: True or False - if True, a new binding will be added,
                    otherwise it will replace a former binding

        """
        raise NotImplementedError

    ############################################################################
    # Special turtle methods

    def begin_poly(self):
        """Not implemented

        Start recording the vertices of a polygon. Current turtle
        position is first vertex of polygon.
        """
        raise NotImplementedError

    def end_poly(self):
        """Not implemented

        Stop recording the vertices of a polygon. Current turtle
        position is last vertex of polygon. This will be connected with
        the first vertex.
        """
        raise NotImplementedError


    def get_poly(self):
        """Not implemented

        Return the last recorded polygon."""
        raise NotImplementedError

    def clone(self):
        """Not implemented

        Create and return a clone of the turtle with same position,
        heading and turtle properties.
        """
        raise NotImplementedError

    def getturtle(self):
        """Not implemented

        Return the Turtle object itself. Only reasonable use: as a
        function to return the "anonymous turtle":
        """
        raise NotImplementedError
    getpen = getturtle

    def getscreen(self):
        """Not implemented

        Return the TurtleScreen object the turtle is drawing
        on. TurtleScreen methods can then be called for that object.
        """
        raise NotImplementedError

    def setundobuffer(self, size):
        """Not implemented

        Set or disable undobuffer. If size is an integer an empty
        undobuffer of given size is installed. size gives the maximum
        number of turtle actions that can be undone by the undo()
        method/function. If size is None, the undobuffer is disabled.

        :param size: an integer or None

        """
        raise NotImplementedError

    def undobufferentries(self):
        """Not implemented

        Return number of entries in the undobuffer."""
        raise NotImplementedError

    ############################################################################
    # Settings and special methods

    def mode(self, mode=None):
        """Not implemented

        Set turtle mode ("standard" or "logo") and perform reset.
        If mode is not given, current mode is returned.

        Mode "standard" is compatible with old turtle.
        Mode "logo" is compatible with most Logo turtle graphics.

        :param mode: one of the strings "standard" or "logo"
        """
        raise NotImplementedError
        # if mode == "standard":
        #     self._logomode = False
        # elif mode == "logo":
        #     self._logomode = True
        # elif mode is None:
        #     if self._logomode:
        #         return "logo"
        #     return "standard"
        # else:
        #     raise RuntimeError("Mode must be 'logo', 'standard!', or None")
        # return None

    def colormode(self, cmode=None):
        """Not implemented

        Return the colormode or set it to 1.0 or 255. Subsequently r,
        g, b values of color triples have to be in the range 0..cmode.

        :param cmode: one of the valkues 1.0 or 255
        """
        raise NotImplementedError

    def getcanvas(self):
        """Not implemented

        Return the Canvas of this TurtleScreen. Useful for insiders
        who know what to do with a Tkinter Canvas.
        """
        raise NotImplementedError

    def getshapes(self):
        """Not implemented

        Return a list of names of all currently available turtle
        shapes.
        """
        raise NotImplementedError

    def register_shape(self, name, shape=None):
        """Not implemented

        There are three different ways to call this function:

        1. name is the name of a gif-file and shape is None: Install the
        corresponding image shape.

        >>> screen.register_shape("turtle.gif")

        Note: Image shapes do not rotate when turning the turtle, so
        they do not display the heading of the turtle!

        2. name is an arbitrary string and shape is a tuple of pairs of
        coordinates: Install the corresponding polygon shape.

        >>> screen.register_shape("triangle", ((5,-3), (0,5), (-5,-3)))

        3. name is an arbitrary string and shape is a (compound) Shape
        object: Install the corresponding compound shape.

        Add a turtle shape to TurtleScreen's shapelist. Only thusly registered
        shapes can be used by issuing the command shape(shapename).
        """
        raise NotImplementedError
    addshape = register_shape

    def turtles(self):
        """Not implemented

        Return the list of turtles on the screen."""
        raise NotImplementedError

    def window_height(self):
        """Not implemented

        Return the height of the turtle window."""
        raise NotImplementedError

    def window_width(self):
        """Not implemented

        Return the width of the turtle window."""
        raise NotImplementedError

    ############################################################################
    # Other

    def _turn(self, angle):
        if self._logomode:
            self._heading -= angle
        else:
            self._heading += angle
        self._heading %= 360         # wrap around
