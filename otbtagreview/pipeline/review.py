import json
from typing import List, Dict, Any

class ReviewGenerator:
    def __init__(self):
        pass
        
    def classify_move(self, prev_eval: float, curr_eval: float, move_idx: int) -> str:
        """
        Classify move based on evaluation drop.
        This is a simplified version.
        prev_eval/curr_eval are CP from White's perspective.
        """
        if prev_eval is None or curr_eval is None:
            return "Book" # Or Unknown
            
        # Determine side to move (if move_idx is even, it was White's move)
        # move_idx 0 = White's first move
        is_white = (move_idx % 2 == 0)
        
        diff = curr_eval - prev_eval
        if not is_white:
            diff = -diff
            
        # Now diff is gain for the side that moved.
        # Usually it's negative (loss of advantage).
        
        if diff <= -300:
            return "Blunder"
        elif diff <= -100:
            return "Mistake"
        elif diff <= -50:
            return "Inaccuracy"
        elif diff >= 50:
            # Opponent blundered previously and we found the best move?
            # Or just "Good" / "Best"
            return "Good"
        else:
            return "Best" # Or Normal
            
    def generate_review(self, game_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        game_data: list of move info (san, fen, eval, etc.)
        """
        # TODO: Implement full review generation
        return {}
