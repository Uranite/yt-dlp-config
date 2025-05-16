import os
import re
import argparse

def extract_youtube_id(filename):
    pattern = r'\[([a-zA-Z0-9_-]{11})\]'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    return None

def main():
    parser = argparse.ArgumentParser(description="Extract YouTube video IDs from filenames.")
    parser.add_argument('-f', '--folder', required=True, help='Folder to scan for filenames')
    parser.add_argument('-o', '--output', required=True, help='Output file to write YouTube IDs')
    args = parser.parse_args()

    youtube_ids = set()
    for filename in os.listdir(args.folder):
        youtube_id = extract_youtube_id(filename)
        if youtube_id:
            youtube_ids.add(youtube_id)

    sorted_ids = sorted(youtube_ids)

    with open(args.output, 'w') as f:
        for youtube_id in sorted_ids:
            f.write(f"youtube {youtube_id}\n")

    print(f"Saved {len(sorted_ids)} YouTube IDs to {args.output}")

if __name__ == "__main__":
    main()
