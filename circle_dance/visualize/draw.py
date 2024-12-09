# general shared drawing functions
import numpy as np
import numpy.typing as npt
import pygame


def draw_circle_alpha(surface, color, center, radius):
    "Helper function to draw a circle with alpha in pygame."
    target_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)


def draw_cone_arc(
    image: npt.NDArray,
    center: tuple[float, float],
    radius: float,
    start_angle_rad: float,
    end_angle_rad: float,
    start_width: float,
    end_width: float,
    color: int = 255,
):
    """
    Draw a solid-color cone-shaped arc on an image.

    Destructively paints on the image, replacing all values under the arc pixels.

    Starts the arc at `start_angle` and ends at `end_angle`. The width of the arc at each point is determined by the
    `start_width` and `end_width` parameters. The width is linearly interpolated between these values.

    The arc is drawn in clock-wise direction.

    Args:
        image: NumPy array representing the image
        center: Tuple (x, y) for the center of the arc
        radius: Radius of the arc
        start_angle_rad: Starting angle in degrees
        end_angle_rad: Ending angle in degrees
        a: Width of the arc at the pointy end (start_angle)
        b: Width of the arc at the broad end (end_angle)
        color: Color of the arc; defaults to 255
    Returns:
        Image with the painted arc
    """
    height, width = image.shape[:2]

    # Create a meshgrid
    y, x = np.ogrid[:height, :width]

    # Calculate distances and angles for each pixel
    dx = x - center[0]
    dy = y - center[1]
    distances = np.sqrt(dx**2 + dy**2)
    angles = np.arctan2(dy, dx)

    # Adjust angles to be in the range [0, 2π]
    angles = (angles + 2 * np.pi) % (2 * np.pi)
    start_angle_rad = (start_angle_rad + 2 * np.pi) % (2 * np.pi)
    end_angle_rad = (end_angle_rad + 2 * np.pi) % (2 * np.pi)

    # Adjust the angular mask to account for wraparound
    if start_angle_rad <= end_angle_rad:
        angle_mask = (angles >= start_angle_rad) & (angles <= end_angle_rad)
    else:  # Wraparound case
        angle_mask = (angles >= start_angle_rad) | (angles <= end_angle_rad)

    # Calculate the angular position within the arc (0 to 1)
    angular_position = np.where(
        angle_mask, (angles - start_angle_rad) % (2 * np.pi) / ((end_angle_rad - start_angle_rad) % (2 * np.pi)), 0
    )

    # Calculate the width at each angular position
    width_at_angle = start_width + (end_width - start_width) * angular_position

    # Create the cone shape
    inner_radius = radius - width_at_angle / 2
    outer_radius = radius + width_at_angle / 2

    # Create the mask for the arc
    arc_mask = (distances >= inner_radius) & (distances <= outer_radius) & angle_mask

    # Apply the mask to create a new image
    # result = np.copy(image)  # !TBD: Maybe not required
    image[arc_mask] = color

    return image


def draw_circular_gradient(width, height):
    """Return an image array with a circular gradient.

    The gradient is black (0) to white (1) along the angle from 0 to 2π.

    Args:
        width: width of the image array to generate
        height: height of the image array to generate

    Returns:
        gradient image array, shape=(width, height), dtype=np.float32
    """
    # Create a grid of x, y coordinates
    y, x = np.ogrid[:width, :height]
    y = y - width // 2
    x = x - height // 2

    # Calculate the angle in radians (0 to 2π) and normalize to 0 to 1 range
    angle = (np.arctan2(-y, x) + 2 * np.pi) % (2 * np.pi)  # Adjust range to 0 to 2π
    normalized_angle = angle / (2 * np.pi)  # Normalize to range [0, 1]

    # Create gradient: black (0) to white (1) along the normalized angle
    gradient = normalized_angle

    return gradient
