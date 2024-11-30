import os
import sys
import re

def extract_youtube_id(filename):
    pattern = r'\[([a-zA-Z0-9_-]{11})\]'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    else:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print("The provided path is not a valid folder.")
        sys.exit(1)
    
    files = os.listdir(folder_path)
    
    new_ids = set()
    for file_name in files:
        youtube_id = extract_youtube_id(file_name)
        if youtube_id:
            new_ids.add(youtube_id)
    
    sorted_ids = sorted(new_ids)
    
    with open('youtube_ids.txt', 'w') as f:
        for youtube_id in sorted_ids:
            f.write(f"youtube {youtube_id}\n")

if __name__ == "__main__":
    main()
