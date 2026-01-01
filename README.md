# OTBTagReview

Convert an over-the-board chess game recorded as a top-down iPhone video into a PGN and a local offline review website.

## Goal

1.  Generate a PGN (SAN) of the game.
2.  Create a local offline “chess.com-like” review website (overview + key moves + coach + follow-up + retry + fix).

## Core Design Choice

Each chess piece has a UNIQUE marker ID (ArUco preferred) attached via a small cap/ring. Detection is marker-based (read IDs), not piece-shape-based. This delivers very high accuracy.

## Requirements

-   **Video**: iPhone top-down, stable mount, entire board visible.
-   **Markers**: 4 corner markers on the board/table to stabilize homography.
-   **Pieces**: Each has a tag ID that maps to a unique piece instance label (e.g., wK, wQ, wP1).
-   **Software**: Python 3.11+, Stockfish (UCI).

## Installation

```bash
pip install -e .
```

## Usage

### 1. Generate ArUco Markers

Use the tool to generate a printable sheet of ArUco markers.

```bash
python -m otbtagreview.tools.generate_aruco_sheet
```

### 2. Create Piece Map

Create a `piece_map.json` mapping tag IDs to pieces.

```bash
python -m otbtagreview.tools.build_piece_map
```

### 3. Analyze Video

```bash
python -m otbtagreview analyze --input <video.mp4> --outdir <outdir> \
  --piece_map <piece_map.json> \
  --use_corner_markers 1 \
  --engine_depth 16 --pv_len 6
```

### 4. Review

Open `index.html` in the output directory to review the game.

## Output Structure

-   `game.pgn`: The game in PGN format.
-   `analysis.json`: Detailed analysis data.
-   `index.html`: Review interface.
-   `debug/`: Debug visuals and logs.

## Troubleshooting

-   **Missing Tags**: Ensure lighting is good and markers are not occluded.
-   **Wrong Square Mapping**: Check corner markers and camera angle.
