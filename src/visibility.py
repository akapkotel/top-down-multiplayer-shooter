#!/usr/bin/env python

from typing import List, Tuple, Sequence

from math import hypot as hypotenuse

import arcade

from game import GameObject


EPSILON = 0.005


def get_segment_bounding_box(segment: Sequence[Tuple]) -> List[Tuple]:
    """
    Helper function for obtaining a bounding box of segment. Allows fast
    checking if two segments intersects.

    :param segment: List
    return: Tuple of tuples
    """
    box = [
        (min(segment[0][0], segment[1][0]), min(segment[0][1], segment[1][1])),
        (max(segment[0][0], segment[1][0]), max(segment[0][1], segment[1][1]))
        ]
    return box


def do_boxes_intersect(a: Tuple[float, float],
                       b: Tuple[float, float],
                       c: Tuple[float, float],
                       d: Tuple[float, float]) -> bool:
    """
    It is known that if bounding boxes
    of two segments do not intersect, segments do not intersect either.
    """
    return a[0] <= d[0] and b[0] >= c[0] and a[1] <= c[1] <= b[1]


def intersects(segment_a: Sequence[Tuple[float, float]],
               segment_b: Sequence[Tuple[float, float]]) -> bool:
    """
    If segment_a is [A, B] and segment_b is [C, D] then segments intersects if
    [A, B, D] is clockwise and [A, B, C] is counter-clockwise, or vice versa.

    :param segment_a: List of tuples -- segment of first segment
    :param segment_b: List of tuples -- segment of second segment
    :return: bool
    """
    a, b = segment_a
    c, d = segment_b

    if are_points_in_line(a, b, c):
        return True

    bounding_box_a = get_segment_bounding_box((a, b))
    bounding_box_b = get_segment_bounding_box((c, d))
    if not do_boxes_intersect(*bounding_box_a, *bounding_box_b):
        return False

    ccw_abc = ccw((a, b, c))
    ccw_abd = ccw((a, b, d))
    ccw_cdb = ccw((c, d, b))
    ccw_cda = ccw((c, d, a))

    return ccw_abc != ccw_abd and ccw_cdb != ccw_cda


def ccw(points_list: Sequence[Tuple[float, float]]) -> bool:
    """
    Check if sequence of points is oriented in clockwise or counterclockwise
    order.
    """
    a, b, c = points_list[0], points_list[1], points_list[2]
    val = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    return val > 0


def are_points_in_line(a: Tuple[float, float],
                       b: Tuple[float, float],
                       c: Tuple[float, float]) -> bool:
    return -EPSILON < (distance(a, c) + distance(c, b) - distance(a, b)) < EPSILON


def distance(coord_a: Tuple, coord_b: Tuple) -> float:
    """
    Calculate distance between two points in 2D space.

    :param coord_a: Tuple -- (x, y) coords of first point
    :param coord_b: Tuple -- (x, y) coords of second p
    :return: float -- 2-dimensional distance between segment
    """
    return hypotenuse(coord_b[0] - coord_a[0], coord_b[1] - coord_a[1])


class VisibleArea:
    def __init__(self):
        self.observer_position = (0, 0)
        self.visible_polygon = []
        self.walls = []

    def __contains__(self, item: GameObject) -> bool:
        x, y = item.position
        if arcade.is_point_in_polygon(x, y, self.visible_polygon):
            visibility_line = self.observer_position, item.position
            return not any(intersects(visibility_line, wall) for wall in self.walls)
        return False

    def update(self, observer_position: Tuple[float, float], visible_area: List, obstacles: List):
        self.observer_position = observer_position
        self.visible_polygon = visible_area
        self.walls.clear()
        for obstacle in obstacles:
            self.walls.extend((obstacle[i], obstacle[i + 1]) for i in range(len(obstacle) - 1))
            self.walls.append((obstacle[-1], obstacle[0]))
