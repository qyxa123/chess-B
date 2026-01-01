import cv2
import click
import json
import numpy as np
from otbtagreview.pipeline.board import BoardWarper
from otbtagreview.pipeline.tags import TagDetector
from otbtagreview.pipeline.mapping import SquareMapper

@click.command()
@click.option('--input', 'input_path', required=True, help='Path to video or image')
@click.option('--corners', required=True, help='Comma-separated list of 4 corner tag IDs (TL,TR,BR,BL)')
@click.option('--output', default='calibration.jpg', help='Output image path')
def main(input_path, corners, output):
    """
    Calibrate board mapping on a sample frame.
    """
    corner_ids = [int(x) for x in corners.split(',')]
    if len(corner_ids) != 4:
        raise ValueError("Must provide exactly 4 corner IDs")
        
    # Read frame
    cap = cv2.VideoCapture(input_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"Could not read from {input_path}")
        return
        
    warper = BoardWarper()
    if not warper.find_corners_and_compute_homography(frame, corner_ids):
        print("Could not find all corner markers")
        return
        
    warped = warper.warp(frame)
    
    # Detect tags on original and warp centers
    detector = TagDetector()
    tags = detector.detect(frame)
    
    if not tags:
        print("No tags detected")
    else:
        # Warp tag centers
        tag_centers = np.array([t.center for t in tags])
        warped_centers = warper.warp_points(tag_centers)
        
        mapper = SquareMapper()
        
        # Draw on warped image
        for i, tag in enumerate(tags):
            wx, wy = warped_centers[i]
            square = mapper.point_to_square(wx, wy)
            
            # Draw point
            cv2.circle(warped, (int(wx), int(wy)), 5, (0, 0, 255), -1)
            
            # Draw label
            label = f"{tag.tag_id}"
            if square:
                label += f":{square}"
            
            cv2.putText(warped, label, (int(wx)+10, int(wy)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    # Draw grid
    for i in range(1, 8):
        pos = int(i * 900 / 8)
        cv2.line(warped, (pos, 0), (pos, 900), (255, 0, 0), 1)
        cv2.line(warped, (0, pos), (900, pos), (255, 0, 0), 1)
        
    cv2.imwrite(output, warped)
    print(f"Calibration image saved to {output}")

if __name__ == '__main__':
    main()
