import board
from adafruit_turtle import turtle, Color

turtle = turtle(board.DISPLAY)
size = min(board.DISPLAY.width, board.DISPLAY.height) * 0.5

print("Turtle time! Lets draw a rainbow benzene")


turtle.pendown()

turtle.dot(20)
turtle.forward(5)
turtle.right(90)
turtle.forward(5)
for _ in range(4):
    turtle.right(90)
    turtle.forward(10)
    # turtle.forward(5)
    # turtle.right(90)
    # turtle.forward(20)
    # turtle.left(90)
    # turtle.forward(5)
    # turtle.left(90)


# turtle.dot(40)
# turtle.left(90)
# turtle.forward(25)
# turtle.dot(30)
# turtle.left(90)
# turtle.forward(25)
# turtle.dot(20)

while True:
    pass
