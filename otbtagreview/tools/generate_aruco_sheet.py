import cv2
import numpy as np
import click
import os

@click.command()
@click.option('--dict', 'dict_type', default='DICT_4X4_50', help='ArUco dictionary type')
@click.option('--start-id', default=0, help='Start ID')
@click.option('--count', default=40, help='Number of markers')
@click.option('--output', default='aruco_sheet.png', help='Output filename')
def main(dict_type, start_id, count, output):
    """
    Generate a sheet of ArUco markers.
    """
    try:
        aruco_dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dict_type))
    except AttributeError:
        print(f"Dictionary {dict_type} not found in cv2.aruco")
        return

    # Grid calculation
    cols = 5
    rows = (count + cols - 1) // cols
    
    marker_size = 200
    margin = 40
    
    width = cols * marker_size + (cols + 1) * margin
    height = rows * marker_size + (rows + 1) * margin
    
    sheet = np.ones((height, width), dtype=np.uint8) * 255
    
    for i in range(count):
        marker_id = start_id + i
        img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
        
        row = i // cols
        col = i % cols
        
        y = margin + row * (marker_size + margin)
        x = margin + col * (marker_size + margin)
        
        sheet[y:y+marker_size, x:x+marker_size] = img
        
        # Add text label
        cv2.putText(sheet, str(marker_id), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        
    cv2.imwrite(output, sheet)
    print(f"Generated {count} markers starting from {start_id} to {output}")

if __name__ == '__main__':
    main()
