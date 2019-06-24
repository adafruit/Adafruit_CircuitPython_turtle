import board
from adafruit_turtle import Color, turtle

turtle = turtle(board.DISPLAY)
print("Turtle time! Lets draw a simple square")

turtle.pencolor(Color.WHITE)
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
