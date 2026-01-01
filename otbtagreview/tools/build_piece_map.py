import json
import click

@click.command()
@click.option('--output', default='piece_map.json', help='Output JSON file')
def main(output):
    """
    Create a default piece map JSON file.
    """
    pieces = [
        "wK", "wQ", "wR1", "wR2", "wB1", "wB2", "wN1", "wN2",
        "wP1", "wP2", "wP3", "wP4", "wP5", "wP6", "wP7", "wP8",
        "bK", "bQ", "bR1", "bR2", "bB1", "bB2", "bN1", "bN2",
        "bP1", "bP2", "bP3", "bP4", "bP5", "bP6", "bP7", "bP8"
    ]
    
    print("This tool helps you create a piece_map.json.")
    print("You will map ArUco tag IDs to chess pieces.")
    print("Enter the Tag ID for each piece (or press Enter to skip/use default if sequential).")
    
    piece_map = {}
    current_id = 0
    
    for piece in pieces:
        val = input(f"Tag ID for {piece} [default {current_id}]: ").strip()
        if val:
            try:
                tag_id = int(val)
            except ValueError:
                print("Invalid ID, using default.")
                tag_id = current_id
        else:
            tag_id = current_id
            
        piece_map[str(tag_id)] = piece
        current_id = tag_id + 1
        
    with open(output, 'w') as f:
        json.dump(piece_map, f, indent=2)
        
    print(f"Saved piece map to {output}")

if __name__ == '__main__':
    main()
