import click
import os
import json
import cv2
import numpy as np
from otbtagreview.pipeline.video import VideoProcessor
from otbtagreview.pipeline.board import BoardWarper
from otbtagreview.pipeline.tags import TagDetector
from otbtagreview.pipeline.mapping import SquareMapper
from otbtagreview.pipeline.states import StateManager
from otbtagreview.pipeline.moves import MoveInferrer

@click.group()
def main():
    pass

@main.command()
@click.option('--input', 'input_path', required=True, help='Path to video file')
@click.option('--outdir', required=True, help='Output directory')
@click.option('--piece_map', required=True, help='Path to piece_map.json')
@click.option('--use_corner_markers', default=1, help='Use corner markers for homography (0 or 1)')
@click.option('--corners', default='0,1,2,3', help='Corner tag IDs (TL,TR,BR,BL) if use_corner_markers=1')
@click.option('--engine_depth', default=16, help='Stockfish analysis depth')
@click.option('--pv_len', default=1, help='PV length for analysis')
def analyze(input_path, outdir, piece_map, use_corner_markers, corners, engine_depth, pv_len):
    """
    Analyze a chess video and generate PGN + review site.
    """
    os.makedirs(outdir, exist_ok=True)
    debug_dir = os.path.join(outdir, 'debug')
    os.makedirs(debug_dir, exist_ok=True)
    
    # 1. Load Piece Map
    with open(piece_map, 'r') as f:
        pmap = json.load(f)
        
    # 2. Initialize Pipeline Components
    video_proc = VideoProcessor(input_path)
    warper = BoardWarper()
    detector = TagDetector()
    mapper = SquareMapper()
    state_mgr = StateManager()
    move_inf = MoveInferrer(pmap)
    
    corner_ids = [int(x) for x in corners.split(',')]
    
    print("Processing video to find stable frames...")
    stable_frames = list(video_proc.get_stable_frames())
    print(f"Found {len(stable_frames)} stable frames.")
    
    if not stable_frames:
        print("No stable frames found!")
        return
        
    # 3. Process each stable frame
    # We assume the first stable frame allows us to lock the homography if the camera is static.
    # Or we recompute per frame if camera moves? 
    # Spec says "stable mount", but "stabilize homography" suggests we might want to be robust.
    # Let's try to compute homography on the first frame and reuse, or recompute if possible.
    # Recomputing per frame is safer if corners are visible.
    
    prev_state = None
    
    # Save debug info
    frame_infos = []
    
    for sf in stable_frames:
        frame_idx = sf.frame_idx
        frame = sf.frame
        
        # 3.1 Warp Board
        # Try to find corners
        has_homography = warper.find_corners_and_compute_homography(frame, corner_ids)
        
        if not has_homography and warper.homography_matrix is None:
            print(f"Frame {frame_idx}: Could not find corners and no previous homography. Skipping.")
            continue
            
        try:
            warped = warper.warp(frame)
        except Exception as e:
            print(f"Frame {frame_idx}: Warp failed {e}")
            continue
            
        # 3.2 Detect Tags on Warped Board (or Original and warp points? Better to detect on Original usually)
        # We detect on original frame for better resolution/quality, then warp centers.
        tags = detector.detect(frame)
        
        # Warp tag centers
        if tags:
            tag_centers = np.array([t.center for t in tags])
            warped_centers = warper.warp_points(tag_centers)
        else:
            warped_centers = []
            
        # 3.3 Map to Squares
        square_tag_map = {} # "e4" -> tag_id
        
        debug_img = warped.copy()
        
        for i, tag in enumerate(tags):
            wx, wy = warped_centers[i]
            sq = mapper.point_to_square(wx, wy)
            
            if sq:
                # Resolve conflict? If multiple tags on same square?
                # Take the one closest to center?
                # For now just overwrite (or could check confidence)
                square_tag_map[sq] = tag.tag_id
                
                # Draw for debug
                cv2.circle(debug_img, (int(wx), int(wy)), 5, (0, 255, 0), -1)
                cv2.putText(debug_img, f"{tag.tag_id}:{sq}", (int(wx), int(wy)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        cv2.imwrite(os.path.join(debug_dir, f"frame_{frame_idx}_warped.jpg"), debug_img)
        
        # 3.4 Create State
        curr_state = state_mgr.create_state(square_tag_map, sf.timestamp, frame_idx)
        
        # 3.5 Infer Move
        if prev_state:
            # Check if state changed significantly?
            # Ideally we only infer move if something changed.
            # But we might have multiple stable frames for the same position.
            # We need to detect *change* of state.
            
            # Simple diff:
            if curr_state.placement != prev_state.placement:
                move = move_inf.infer_move(prev_state, curr_state)
                if move:
                    print(f" inferred move: {move} at {sf.timestamp:.2f}s")
                else:
                    print(f" state changed but no valid move found at {sf.timestamp:.2f}s")
            else:
                # No change
                pass
        
        prev_state = curr_state
        
    # 4. Output PGN
    pgn_path = os.path.join(outdir, "game.pgn")
    with open(pgn_path, "w") as f:
        f.write(move_inf.get_pgn())
    print(f"PGN saved to {pgn_path}")
    
    # 5. Stockfish Analysis (MVP-3)
    from otbtagreview.pipeline.engine import EngineAnalyzer
    from otbtagreview.pipeline.review import ReviewGenerator
    
    # Initialize engine
    engine = EngineAnalyzer(depth=engine_depth)
    engine.start()
    
    # Analyze the game from PGN
    # Reload game from PGN to be sure we have clean history
    import chess.pgn
    import io
    
    pgn_str = move_inf.get_pgn()
    pgn_io = io.StringIO(pgn_str)
    game = chess.pgn.read_game(pgn_io)
    
    analyzed_moves = []
    
    if game and engine.engine:
        board = game.board()
        prev_eval = None
        
        review_gen = ReviewGenerator()
        
        print("Running Stockfish analysis...")
        
        # Analyze initial position? Usually not needed unless custom start.
        
        move_idx = 0
        for node in game.mainline():
            move = node.move
            board.push(move)
            
            # Analyze position after move
            eval_result = engine.analyze(board, pv_len=pv_len)
            
            # Classify
            curr_cp = eval_result.get("score_cp")
            classification = review_gen.classify_move(prev_eval, curr_cp, move_idx)
            
            analyzed_moves.append({
                "san": node.san(),
                "uci": move.uci(),
                "fen": board.fen(),
                "eval": eval_result,
                "classification": classification
            })
            
            prev_eval = curr_cp
            move_idx += 1
            print(f" Analyzed move {move_idx}: {node.san()} ({classification})")
            
    engine.stop()

    # 6. Generate Web Assets
    analysis = {
        "moves": analyzed_moves,
        "game_info": game.headers if game else {}
    }
    
    # Write JSON for reference
    with open(os.path.join(outdir, "analysis.json"), "w") as f:
        json.dump(analysis, f, indent=2)
        
    # Write JS for local file access (avoid CORS)
    with open(os.path.join(outdir, "data.js"), "w") as f:
        f.write("window.GAME_DATA = " + json.dumps(analysis, indent=2) + ";")
        
    # Copy web assets
    import shutil
    # Assuming web assets are relative to package
    # For now, just copy the index.html we wrote
    # But ideally we should package it.
    # Since we are running from source or installed package...
    # Let's write the index.html content directly or copy if it exists in source
    
    # For now, we manually wrote index.html in the previous step to source.
    # We should copy it to outdir.
    src_web = os.path.join(os.path.dirname(__file__), 'web', 'index.html')
    if os.path.exists(src_web):
        shutil.copy(src_web, os.path.join(outdir, 'index.html'))
    else:
        print("Warning: index.html template not found!")

if __name__ == '__main__':
    main()
