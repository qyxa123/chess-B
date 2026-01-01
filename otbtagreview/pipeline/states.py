from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class BoardState:
    # Map square (e.g., "e4") to piece tag ID (e.g., 12)
    placement: Dict[str, int]
    timestamp: float
    frame_idx: int
    
    def to_dict(self):
        return {
            "placement": self.placement,
            "timestamp": self.timestamp,
            "frame_idx": self.frame_idx
        }

class StateManager:
    def __init__(self):
        self.history: List[BoardState] = []
        
    def create_state(self, square_tag_map: Dict[str, int], timestamp: float, frame_idx: int) -> BoardState:
        state = BoardState(placement=square_tag_map, timestamp=timestamp, frame_idx=frame_idx)
        self.history.append(state)
        return state
