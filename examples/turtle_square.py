import board
from Adafruit_CircuitPython_turtle.adafruit_turtle import *

turtle = turtle(board.DISPLAY)
print("Turtle time! Lets draw a simple square")

turtle.pencolor(color.WHITE)
print("Position:", turtle.pos())
print("Heading:", turtle.heading())

turtle.penup()
print("Pen down?", turtle.isdown())
turtle.pendown()
print("Pen down?", turtle.isdown())
turtle.forward(25)
print("Position:", turtle.pos())
turtle.left(90)
turtle.forward(25)
print("Position:", turtle.pos())
turtle.left(90)
turtle.forward(25)
print("Position:", turtle.pos())
turtle.left(90)
turtle.forward(25)
print("Position:", turtle.pos())

while True:
    pass
