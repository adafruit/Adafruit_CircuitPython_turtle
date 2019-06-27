import board
from adafruit_turtle import Color, turtle

turtle = turtle(board.DISPLAY)

turtle.pencolor(Color.WHITE)

turtle.pendown()
turtle.circle(20)
turtle.forward(20)
turtle.circle(20, extent=180)
turtle.forward(50)
turtle.circle(50, steps=6)
while True:
    pass
