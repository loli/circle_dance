# circular sheet visualization: utility functions

import math

from circle_dance.visualize.circular_sheet import config


def get_angle_at_time(t: float) -> float:
    """Get the rotation angle in radians at a certain time in second."""
    return (t % config.rotation_period) * (2 * math.pi / config.rotation_period)
