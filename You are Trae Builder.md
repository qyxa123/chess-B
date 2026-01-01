You are Trae Builder. Create a brand-new, runnable project from scratch: “OTBTagReview”.
Goal: Convert an over-the-board chess game recorded as a top-down iPhone video into:
1) a PGN (SAN) of the game, and
2) a local offline “chess.com-like” review website (overview + key moves + coach + follow-up + retry + fix).

Core design choice: Each chess piece has a UNIQUE marker ID (ArUco preferred) attached via a small cap/ring. Detection is marker-based (read IDs), not piece-shape-based. This should deliver very high accuracy.

==================================================
0) Hard Requirements (must satisfy)
==================================================
- Player experience: During play, user does NOTHING except start recording and stop recording.
- Post-game: ONE command generates outputs:
  - game.pgn
  - analysis.json
  - index.html (offline review website)
  - debug/ folder with visuals/logs
- Offline & free: Use local Stockfish (UCI). No cloud, no chess.com premium.
- Must handle full chess rules: capture, castling, en passant, promotions.
- Must include a correction workflow: when a move is uncertain / missing markers, user can fix in the web UI (choose correct move from candidates, or correct board state), then pipeline recomputes from that step onward.
- Accuracy first: Provide robust board normalization (homography) and robust tag → square mapping.
- Implement in Python 3.11+. Frontend must work by opening index.html locally (no server required).

==================================================
1) Video + Marker Setup assumptions
==================================================
- Video: iPhone top-down, stable mount, entire board visible.
- OPTIONAL but strongly recommended: 4 corner markers on the board/table to stabilize homography.
- Pieces: each has a tag ID that maps to a unique piece instance label like:
  wK, wQ, wR1, wR2, wB1, wB2, wN1, wN2, wP1..wP8
  bK, bQ, bR1.., bP1..bP8
- Provide a tool to generate and print ArUco markers and a tool to create piece_map.json.

==================================================
2) Deliverables (must produce)
==================================================
A) Repository with this structure:
otbtagreview/
  __init__.py
  cli.py
  config.py
  io/
    paths.py
    manifests.py
  pipeline/
    video.py          # decode + motion metric + stable frame selection
    board.py          # board detection + homography + grid overlay
    tags.py           # aruco detection + tag confidence + annotate frames
    mapping.py        # map tag centers to squares; calibration utilities
    states.py         # represent board state (piece->square), temporal smoothing
    moves.py          # infer legal moves from consecutive states using python-chess
    pgn.py            # PGN writer and SAN conversion
    engine.py         # stockfish UCI runner
    review.py         # eval graph, classification, key moves, coach text, PV lines
    cache.py          # caching analysis results per position for speed
  web/
    index.html
    app.js
    styles.css
    assets/
  tools/
    generate_aruco_sheet.py   # outputs printable PNG/PDF sheet of tags
    build_piece_map.py        # helper to create piece_map.json
    calibrate_board.py        # overlay grid, validate square mapping on a sample frame
  tests/
    test_square_mapping.py
    test_move_inference.py
README.md
pyproject.toml (or requirements.txt)

B) CLI (must work):
1) Analyze a single video:
   python -m otbtagreview analyze --input <video.mp4> --outdir <outdir> \
     --piece_map <piece_map.json> \
     --use_corner_markers 1 \
     --engine_depth 16 --pv_len 6

2) Watch an inbox folder:
   python -m otbtagreview watch --inbox <dir> --outroot <dir> --piece_map <piece_map.json>

C) Output contract (outdir):
- game.pgn
- analysis.json (moves, evals, categories, keyMoves, coach, PV)
- web/ (or index.html + assets)
- debug/
   stable_frames/
   motion_plot.json
   warped_boards/
   grid_overlays/
   tag_annotated/
   tag_json/
   state_json/
   diffs/
   step_confidence.json
- manifest.json (run metadata, params)

D) README must include:
- Hardware/recording checklist (lighting, angle, lock AE/AF, avoid glare)
- How to print markers and attach to pieces using caps/rings
- How to create piece_map.json
- How to run analyze/watch
- How to open review page
- Debugging guide (what to inspect when it fails)
- Troubleshooting (missing tags, blur, wrong square mapping)

==================================================
3) Core Pipeline Specs (must implement)
==================================================
3.1 Stable frame selection (no per-move button)
- Compute motion metric per frame (absdiff mean or optical flow magnitude).
- Define stable when motion < threshold continuously for N frames (~0.5–1.0s).
- Select a representative frame (middle of stable segment).
- Export stable frames and motion plot.

3.2 Board normalization
Two modes:
- Mode A (recommended): detect 4 corner markers → homography → warp to 900x900
- Mode B (fallback): detect board boundary/grid from image (run but may be weaker)
Always output grid overlay images to verify alignment.

3.3 Tag detection
- Use OpenCV aruco:
  - detectMarkers + estimatePoseSingleMarkers if useful
- For each stable frame:
  - detect tag IDs + corners + confidence/quality score
  - annotate warped board with tag bounding boxes and IDs
- Provide temporal smoothing:
  - if a tag disappears briefly, carry forward last known square if motion low and other tags stable.

3.4 Tag-to-square mapping (critical)
- After warping, mapping is simple:
  - square_size = warped_size / 8
  - file = floor(x / square_size)
  - rank = 7 - floor(y / square_size) (white at bottom)
- Provide calibration utility that shows:
  - warped frame + grid + each tag labeled with computed square (e.g., “23 → e4”)
  - a way to flip orientation if camera rotated

3.5 Move inference (python-chess)
- Convert state[t] and state[t+1] to a legal move from board position.
- Must handle:
  - capture: one piece disappears (captured)
  - castling: king+rook move
  - en passant: pawn captured off the destination square
  - promotion: pawn replaced by new piece type
- Since tags identify piece instances (e.g., wP3), promotion needs a plan:
  - either user swaps the cap to a new tag for the promoted piece
  - or allow “promotion override” in correction UI when pawn reaches last rank
Implement promotion logic and document the required user action.

If multiple legal moves match, rank candidates by:
- minimal discrepancy between predicted next state and observed state
- tag detection confidence
- optional shallow engine tie-break (very fast)

3.6 Uncertainty & correction
- Compute per-step confidence.
- Mark a step uncertain if:
  - missing critical tags
  - multiple candidate moves close score
  - large mismatch between predicted and observed
- In analysis.json include:
  - uncertainSteps: [ {ply, reason, candidates:[...]} ]
- Web UI must allow:
  - pick correct move from candidates
  - recompute from that ply forward and regenerate PGN/analysis

3.7 Stockfish analysis & review features
- Run Stockfish (local UCI):
  - depth configurable
  - output eval (cp/mate) and PV line (pv_len)
- Compute:
  - eval graph points
  - move classification:
    Best / Good / Inaccuracy / Mistake / Blunder
    + Book, Miss (minimum)
  - key moves selection:
    last book move, largest swing, blunders/mistakes/misses
  - coach text (template-based but concrete):
    mention threats, hanging piece, missed tactic, etc.
  - follow-up playback: PV line
  - retry: user tries best move at key position, get hint and grading

==================================================
4) Frontend (must be offline, open index.html)
==================================================
- Single-page app (vanilla JS ok).
- Load analysis.json + game.pgn (or combined game.json).
- Provide:
  - board replay + move list
  - eval bar + eval graph (click to jump)
  - per-move icons/labels (e.g., ?, ??, !)
  - “Next key move”
  - “Show follow-up” / “Hide”
  - “Retry” interactive move input (click-from/to squares)
  - “Fix” UI for uncertain steps (candidate list)

Use a lightweight chessboard rendering:
- Option 1: chessboard.js + chess.js (fine)
- Option 2: custom canvas (also fine)

==================================================
5) Build Plan (must implement in order)
==================================================
MVP-1: stable frames + warp + tag detection + state export + calibration tool
MVP-2: move inference + PGN generation + basic replay page
MVP-3: s

