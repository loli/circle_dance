# circular sheet visualization: configuration

# Colors
BLACK = (0, 0, 0)
PINK = (255, 105, 180)
sheet_colors = [
    (255, 0, 126),
    (221, 7, 127),
    (187, 14, 128),
    (152, 21, 128),
    (118, 28, 129),
    (84, 35, 130),
]


# rotation
rotation_period = 10  # seconds for a full rotation

# sheets
n_notes: int = 12  # including half-notes
n_sheet_lines: int = n_notes // 2  # corresponds to full notes
max_dist_between_sheet_lines: int = (
    15  # maximum distance between each two lines of a sheet; to avoid too spread out sheet lines when few sheets on canvas
)

# canvas
radius_margin_outer: int = 100  # space in pixels to leave between screen and first sheet
radius_margin_inner: int = 50  # space in pixels to leave between screen and last sheet
n_lines_space_between_sheets: int = 3  # number of sheet lines of space to leave between each two sheets
