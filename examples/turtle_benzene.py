import board
from Adafruit_CircuitPython_turtle.adafruit_turtle import *

turtle = turtle(board.DISPLAY)
benzsize = min(board.DISPLAY.width, board.DISPLAY.height) * 0.9  # 90% of screensize

print("Turtle time! Lets draw a rainbow benzene")

colors = (Color.RED, Color.ORANGE, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE)

turtle.pendown()
start = turtle.pos()

for x in range(66):
    turtle.pencolor(colors[x%6])
    turtle.forward(x)
    turtle.left(59)

while True:
    pass
