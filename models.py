class Point:
    def __init__(self, x, y, name=None):
        self.x = float(x)
        self.y = float(y)
        self.name = name

class Line:
    # defined by two points (references)
    def __init__(self, p1: Point, p2: Point):
        self.p1 = p1
        self.p2 = p2

class Circle:
    def __init__(self, center: Point, radius: float):
        self.center = center
        self.radius = float(radius)

class PlotFunc:
    def __init__(self, expr: str):
        self.expr = expr  # string expression, evaluated with x in locals

