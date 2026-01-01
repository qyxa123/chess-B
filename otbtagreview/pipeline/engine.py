import chess
import chess.engine
import os
from typing import List, Dict, Optional, Any

class EngineAnalyzer:
    def __init__(self, engine_path: str = "stockfish", depth: int = 16, threads: int = 2):
        self.engine_path = engine_path
        self.depth = depth
        self.threads = threads
        self.engine = None
        
    def start(self):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            self.engine.configure({"Threads": self.threads})
        except FileNotFoundError:
            print(f"Warning: Stockfish engine not found at {self.engine_path}. Analysis will be skipped.")
            self.engine = None
            
    def stop(self):
        if self.engine:
            self.engine.quit()
            
    def analyze(self, board: chess.Board, pv_len: int = 1) -> Dict[str, Any]:
        if not self.engine:
            return {}
            
        info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth), multipv=pv_len)
        
        # Format result
        # Note: info is a list if multipv > 1, but we usually take the best line
        if isinstance(info, list):
            best_info = info[0]
        else:
            best_info = info
            
        score = best_info["score"].white() # Always from white's perspective for graph?
        # Or usually cp is relative to side to move.
        # Let's store both or standardized.
        # python-chess score.white() gives score from white's POV.
        
        mate = score.mate()
        cp = score.score()
        
        pv_moves = best_info.get("pv", [])
        pv_san = []
        
        # We need a temp board to generate SAN for PV
        temp_board = board.copy()
        for move in pv_moves:
            pv_san.append(temp_board.san(move))
            temp_board.push(move)
            
        return {
            "score_cp": cp,
            "score_mate": mate,
            "depth": best_info.get("depth", 0),
            "pv": pv_san,
            "best_move": pv_moves[0].uci() if pv_moves else None
        }
