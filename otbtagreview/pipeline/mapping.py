import numpy as np
from typing import Tuple, Optional

class SquareMapper:
    def __init__(self, board_size: int = 900, white_at_bottom: bool = True):
        self.board_size = board_size
        self.square_size = board_size / 8.0
        self.white_at_bottom = white_at_bottom
        
    def point_to_square(self, x: float, y: float) -> Optional[str]:
        """
        Convert (x, y) on warped board to algebraic notation (e.g., "e4").
        Returns None if out of bounds.
        """
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return None
            
        col = int(x // self.square_size)
        row = int(y // self.square_size)
        
        # Clamp just in case
        col = max(0, min(7, col))
        row = max(0, min(7, row))
        
        if self.white_at_bottom:
            file_idx = col
            rank_idx = 7 - row
        else:
            file_idx = 7 - col
            rank_idx = row
            
        files = "abcdefgh"
        ranks = "12345678"
        
        return f"{files[file_idx]}{ranks[rank_idx]}"
        
    def square_to_center(self, square: str) -> Tuple[float, float]:
        """
        Convert algebraic square (e.g., "e4") to center (x, y).
        """
        files = "abcdefgh"
        ranks = "12345678"
        
        if len(square) != 2:
            raise ValueError(f"Invalid square: {square}")
            
        f = files.index(square[0])
        r = ranks.index(square[1])
        
        if self.white_at_bottom:
            col = f
            row = 7 - r
        else:
            col = 7 - f
            row = r
            
        x = (col + 0.5) * self.square_size
        y = (row + 0.5) * self.square_size
        return (x, y)
