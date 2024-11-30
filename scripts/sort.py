import sys
import os

def is_text_file(file_path):
    return os.path.isfile(file_path) and file_path.endswith('.txt')

def sort_youtube_ids(input_file):
    if not is_text_file(input_file):
        print("Error: Input must be a text file with a .txt extension.")
        sys.exit(1)

    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

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

    try:
        with open(input_file, 'w') as f:
            f.writelines(sorted_lines)
    except IOError as e:
        print(f"Error writing to file: {e}")
        sys.exit(1)

    print(f"Sorted YouTube video IDs have been written back to {input_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python sort.py input_file.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    sort_youtube_ids(input_file)

if __name__ == "__main__":
    main()
