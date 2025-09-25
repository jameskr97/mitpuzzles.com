# Dynamic Board

This directory contains `board.*.vue` which make up the dynamic grid, with the following features:

- "Gutters", which are additional rows that are to the top, bottom, left, and right of the grid. These gutters will stay inline with the base-grid (and inherit any dynamic widths that are parallel to the main game grid.). These gutters can be individually indexed.
- Customizable border styling: Each grid cell has a connecting line that can be styled, such as to mark some state between the two cells.
- Dynamic number of rows and columns
- Dynamic cell size
- Optional n-based grid border thickness

## Known Issues

- The outer border thickness is not included in board width and height calculations.
  - This is most noticeable when the outside border is thick.
  - Side Effects:
    - When the outer border is large, it will cause the board to shift to the right.
    - The interaction overlay will be smaller than the board (by exactly the size of the outer border).
