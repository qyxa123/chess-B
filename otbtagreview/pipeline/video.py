import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Generator, Tuple

@dataclass
class StableFrame:
    frame: np.ndarray
    frame_idx: int
    timestamp: float
    motion_score: float

class VideoProcessor:
    def __init__(self, video_path: str, motion_threshold: float = 5.0, stable_duration: float = 0.5):
        self.video_path = video_path
        self.motion_threshold = motion_threshold
        self.stable_duration = stable_duration
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 30.0 # Fallback
        self.min_stable_frames = int(self.stable_duration * self.fps)

    def get_stable_frames(self) -> Generator[StableFrame, None, None]:
        prev_frame = None
        stable_sequence = []
        frame_idx = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            score = 1000.0
            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                score = np.mean(diff)
            
            prev_frame = gray
            
            if score < self.motion_threshold:
                stable_sequence.append((frame.copy(), frame_idx, score))
            else:
                if len(stable_sequence) >= self.min_stable_frames:
                    # Yield the middle frame of the stable sequence
                    mid_idx = len(stable_sequence) // 2
                    best_frame, best_idx, best_score = stable_sequence[mid_idx]
                    yield StableFrame(
                        frame=best_frame,
                        frame_idx=best_idx,
                        timestamp=best_idx / self.fps,
                        motion_score=best_score
                    )
                stable_sequence = []
                
            frame_idx += 1
            
        # Check end of video
        if len(stable_sequence) >= self.min_stable_frames:
            mid_idx = len(stable_sequence) // 2
            best_frame, best_idx, best_score = stable_sequence[mid_idx]
            yield StableFrame(
                frame=best_frame,
                frame_idx=best_idx,
                timestamp=best_idx / self.fps,
                motion_score=best_score
            )
            
    def release(self):
        self.cap.release()
