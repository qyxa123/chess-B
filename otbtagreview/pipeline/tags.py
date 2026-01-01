import cv2
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class DetectedTag:
    tag_id: int
    center: Tuple[float, float]
    corners: np.ndarray
    confidence: float = 1.0 

class TagDetector:
    def __init__(self, dict_type=cv2.aruco.DICT_4X4_50):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(dict_type)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.parameters)
        
    def detect(self, frame: np.ndarray) -> List[DetectedTag]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        results = []
        if ids is not None:
            ids = ids.flatten()
            for i, marker_id in enumerate(ids):
                c = corners[i][0] # (4, 2)
                center = np.mean(c, axis=0)
                results.append(DetectedTag(
                    tag_id=int(marker_id),
                    center=(float(center[0]), float(center[1])),
                    corners=c
                ))
        return results
