import sys
import os

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
    if len(sys.argv) < 2:
        print("Usage: python sort.py input_file.txt")
        sys.exit(1)

    sort_youtube_ids(sys.argv[1])

if __name__ == "__main__":
    main()
