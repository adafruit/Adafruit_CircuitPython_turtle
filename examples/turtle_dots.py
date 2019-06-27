import board
from adafruit_turtle import turtle, Color

turtle = turtle(board.DISPLAY)
size = min(board.DISPLAY.width, board.DISPLAY.height) * 0.5

print("Turtle time! Lets draw a rainbow benzene")


turtle.pendown()

for _ in range(4):
    turtle.dot(8, Color.RED)
    turtle.left(90)
    turtle.forward(25)

while True:
    pass
