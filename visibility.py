#!/usr/bin/env python

from typing import List, Tuple

from arcade import is_point_in_polygon

from game import GameObject


class VisibleArea:
    def __init__(self):
        self.observer_position = (0, 0)
        self.obstacles = []
        self.visibility_polygon: List[Tuple] = []

    def __contains__(self, item: GameObject) -> bool:
        x, y = item.position
        return is_point_in_polygon(x, y, self.visibility_polygon)

    def update(self, observer_position: Tuple[float, float], obstacles: List):
        # TODO: check if any obstacle is blocking observer's field-of-view shadowing a portion of the screen and update
        #  the visibility polygon
        self.observer_position = observer_position
        self.obstacles = obstacles
