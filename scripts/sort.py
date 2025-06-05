import os
import argparse

def sort_youtube_ids(input_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    video_ids = []
    for line in lines:
        line = line.strip()
        if line.startswith('youtube '):
            parts = line.split(' ', 1)
            if len(parts) == 2:
                video_id = parts[1]
                video_ids.append(video_id)

    sorted_ids = sorted(video_ids)

    sorted_lines = [f"youtube {vid}\n" for vid in sorted_ids]

    with open(input_file, 'w') as f:
        f.writelines(sorted_lines)

    print(f"Sorted YouTube video IDs have been written back to {input_file}")

def main():
    parser = argparse.ArgumentParser(description='Sort YouTube video IDs in a file.')
    parser.add_argument('input_file', help='Path to the input file containing YouTube video IDs')
    
    args = parser.parse_args()
    sort_youtube_ids(args.input_file)

if __name__ == "__main__":
    main()
