import cv2
import numpy as np
from typing import Optional, List, Tuple

class BoardWarper:
    def __init__(self, output_size: int = 900):
        self.output_size = output_size
        self.homography_matrix = None
        
    def find_corners_and_compute_homography(self, frame: np.ndarray, corner_ids: List[int], aruco_dict_type=cv2.aruco.DICT_4X4_50) -> bool:
        """
        Detect 4 corner markers to compute homography.
        Assumes corner_ids are ordered: [TopLeft, TopRight, BottomRight, BottomLeft]
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        
        corners, ids, rejected = detector.detectMarkers(gray)
        
        if ids is None:
            return False
            
        # Map detected IDs to their centers
        found_corners = {}
        ids = ids.flatten()
        for i, marker_id in enumerate(ids):
            if marker_id in corner_ids:
                # corners[i] is shape (1, 4, 2)
                c = corners[i][0]
                center = np.mean(c, axis=0)
                found_corners[marker_id] = center
                
        if len(found_corners) != 4:
            return False
            
        src_points = []
        for cid in corner_ids:
            if cid not in found_corners:
                return False
            src_points.append(found_corners[cid])
            
        src_points = np.array(src_points, dtype=np.float32)
        
        # Destination points: 0,0 -> 900,0 -> 900,900 -> 0,900
        # This maps the *centers* of the corner markers to the corners of the 900x900 image.
        # This assumes the markers are exactly at the corners of the play area.
        dst_points = np.array([
            [0, 0],
            [self.output_size, 0],
            [self.output_size, self.output_size],
            [0, self.output_size]
        ], dtype=np.float32)
        
        self.homography_matrix, _ = cv2.findHomography(src_points, dst_points)
        return True
        
    def warp(self, frame: np.ndarray) -> np.ndarray:
        if self.homography_matrix is None:
            raise ValueError("Homography matrix not computed")
        return cv2.warpPerspective(frame, self.homography_matrix, (self.output_size, self.output_size))
        
    def warp_points(self, points: np.ndarray) -> np.ndarray:
        """
        Warp a list of points (N, 2).
        """
        if self.homography_matrix is None:
            raise ValueError("Homography matrix not computed")
            
        # cv2.perspectiveTransform requires shape (N, 1, 2)
        if len(points) == 0:
            return points
        pts = points.reshape(-1, 1, 2).astype(np.float32)
        dst = cv2.perspectiveTransform(pts, self.homography_matrix)
        return dst.reshape(-1, 2)
