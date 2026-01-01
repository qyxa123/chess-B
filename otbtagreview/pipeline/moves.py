import chess
import chess.pgn
from typing import List, Optional, Dict, Tuple, Set
from .states import BoardState

class MoveInferrer:
    def __init__(self, piece_map: Dict[str, str]):
        """
        piece_map: tag_id (str) -> piece_label (e.g. "wK", "wP1")
        """
        self.piece_map = piece_map
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.node = self.game
        
    def infer_move(self, prev_state: BoardState, curr_state: BoardState) -> Optional[chess.Move]:
        """
        Compare two states and find the legal move that explains the transition.
        """
        prev_map = prev_state.placement
        curr_map = curr_state.placement
        
        best_move = None
        min_discrepancy = float('inf')
        
        # Optimization: Identify likely source/dest squares to prune search?
        # For now, brute force over legal moves (~30 moves) is fast enough.
        
        for move in self.board.legal_moves:
            # Construct expected placement for this move
            expected_map = prev_map.copy()
            
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)
            
            # Move the tag
            mover_tag = expected_map.get(from_sq)
            if mover_tag is None:
                # If we think a piece moved from here, but we didn't have a tag there,
                # this move is unlikely unless our prev state was missing a tag.
                # Let's penalize this but not strictly forbid (robustness).
                # discrepancy += 1 implicitly because expected_map won't have the tag at to_sq?
                # Actually if mover_tag is None, expected_map[to_sq] will be None (or whatever was there).
                # If there was a capture, we overwrite.
                pass
            else:
                del expected_map[from_sq]
                expected_map[to_sq] = mover_tag # Overwrites capture
            
            # Handle Castling
            if self.board.is_castling(move):
                if move.to_square == chess.G1:
                    r_from, r_to = "h1", "f1"
                elif move.to_square == chess.C1:
                    r_from, r_to = "a1", "d1"
                elif move.to_square == chess.G8:
                    r_from, r_to = "h8", "f8"
                elif move.to_square == chess.C8:
                    r_from, r_to = "a8", "d8"
                else:
                    r_from, r_to = None, None
                
                if r_from:
                    rook_tag = expected_map.get(r_from)
                    if rook_tag:
                        del expected_map[r_from]
                        expected_map[r_to] = rook_tag
            
            # Handle En Passant
            if self.board.is_en_passant(move):
                # Captured pawn is at (to_file, from_rank)
                ep_square_idx = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
                ep_sq = chess.square_name(ep_square_idx)
                if ep_sq in expected_map:
                    del expected_map[ep_sq]
            
            # Compare expected_map with curr_map
            discrepancy = 0
            
            all_sqs = set(expected_map.keys()) | set(curr_map.keys())
            for sq in all_sqs:
                exp_tag = expected_map.get(sq)
                obs_tag = curr_map.get(sq)
                
                if exp_tag != obs_tag:
                    discrepancy += 1
            
            # Bonus: if mover_tag matches obs_tag at to_sq, it's a strong signal.
            # But discrepancy already covers this.
            
            if discrepancy < min_discrepancy:
                min_discrepancy = discrepancy
                best_move = move
                
        # Heuristic threshold: if discrepancy is too high, maybe no valid move found?
        # But we must pick the best legal move if possible.
        # Let's trust the min discrepancy.
        
        if best_move:
            self.board.push(best_move)
            self.node = self.node.add_variation(best_move)
            return best_move
            
        return None
        
    def get_pgn(self) -> str:
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        return self.game.accept(exporter)
