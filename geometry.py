#!/usr/bin/env python

import math

from typing import Tuple


def move_along_vector(start: Tuple, velocity: float, target: Tuple = None) -> Tuple:
    """
    Create movement vector starting at 'start' point angled in direction of
    'target' point with scalar velocity 'velocity'. Optionally, instead of
    'target' position, you can pass starting 'angle' of the vector.

    Use 'current_waypoint' position only, when you now the point and do not know the
    angle between two points, but want quickly calculate position of the
    another point lying on the line connecting two, known points.

    :param start: tuple -- point from vector starts
    :param target: tuple -- current_waypoint that vector 'looks at'
    :param velocity: float -- scalar length of the vector
    :return: tuple -- (optional)position of the vector end
    """
    p1 = (start[0], start[1])
    if target:
        p2 = (target[0], target[1])
        angle = calculate_angle(*p1, *p2)
    vector = vector_2d(angle, velocity)
    return p1[0] + vector[0], p1[1] + vector[1]


def calculate_angle(sx: float, sy: float, ex: float, ey: float) -> float:
    """
    Calculate angle in direction from 'start' to the 'end' point in degrees.
    """
    rads = math.atan2(ex - sx, ey - sy)
    return -math.degrees(rads) % 360


def vector_2d(angle: float, scalar: float) -> Tuple:
    rad = -math.radians(angle)
    return math.sin(rad) * scalar, math.cos(rad) * scalar
