import os
import re
import shutil
import argparse
import subprocess
from datetime import datetime
import yt_dlp
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube import _video

def extract_info_from_filename(filename):
    id_match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', filename)
    itag_match = re.search(r'\[(\d+)\+\d+\]', filename)
    if id_match and itag_match:
        return id_match.group(1), itag_match.group(1)
    return None, None

def get_master_format_rankings():
    formats = _video.YoutubeIE._formats
    formats_list = []
    for itag, fmt in formats.items():
        fmt = fmt.copy()
        fmt['format_id'] = str(itag)
        if 'url' not in fmt:
            fmt['url'] = f'https://dummy/{itag}' # Hope this doesn't cause the sorting to be innacurate
        formats_list.append(fmt)

    info_dict = {'formats': formats_list}

    ydl = YoutubeDL(params={})
    ydl.sort_formats(info_dict)

    itag_rank_map = {}
    current_rank = 1
    for fmt in reversed(info_dict['formats']): # Best to worst
        itag = fmt['format_id']
        if itag == '616':
            continue
        itag_rank_map[itag] = current_rank
        current_rank += 1

    itag_rank_map['616'] = 0
    return itag_rank_map

def get_best_live_itag(youtube_id):
    url = f"https://www.youtube.com/watch?v={youtube_id}"
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info['formats']
            best_format = formats[-1]
            return best_format['format_id']
        except Exception as e:
            print(f"Error fetching info for {youtube_id}: {e}")
            return None

def move_files_by_video_id(src_folder, dest_folder, video_id):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    moved = []
    for filename in os.listdir(src_folder):
        if f"[{video_id}]" in filename:
            src = os.path.join(src_folder, filename)
            dest = os.path.join(dest_folder, filename)
            shutil.move(src, dest)
            moved.append(filename)
    return moved

def perform_redownload(args, yt_id, folder, backup_root, redownload_dir, dry_run):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(backup_root, f"{yt_id}_{timestamp}")
    
    print(f"\n[INFO] Redownloading {yt_id}, backing up to {backup_dir}")
    
    if dry_run:
        return

    moved_files = move_files_by_video_id(folder, backup_dir, yt_id)
    if not moved_files:
        print(f"[WARN] No files found to back up for {yt_id}. Skipping.")
        return

    try:
        url = f"https://www.youtube.com/watch?v={yt_id}"
        subprocess.run([
            'yt-dlp', url,
            '--config-location', args.config,
            '-P', redownload_dir
        ], check=True)

        downloaded_files = [f for f in os.listdir(redownload_dir) if f"[{yt_id}]" in f]
        if not downloaded_files:
            print(f"[ERROR] Redownload failed for {yt_id}. Backup preserved at: {backup_dir}")
            return

        for f in downloaded_files:
            shutil.move(os.path.join(redownload_dir, f), os.path.join(folder, f))

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] yt-dlp failed for {yt_id}: {e}. Backup at: {backup_dir}")
    finally:
        for f in os.listdir(redownload_dir):
            os.remove(os.path.join(redownload_dir, f))

def main():
    parser = argparse.ArgumentParser(description="Compare and optionally redownload YouTube videos if current format is worse than best live format.")
    parser.add_argument('-f', '--folder', required=True, help='Folder containing downloaded videos (non-recursive)')
    parser.add_argument('-o', '--output', required=True, help='Output text file for logging')
    parser.add_argument('--redownload', action='store_true', help='Redownload videos if current format is worse than best live format')
    parser.add_argument('--dry-run', action='store_true', help='Simulate actions without modifying files')
    parser.add_argument('--config', default='yt-dlp.conf', help='Path to yt-dlp configuration file')
    parser.add_argument('--backup-dir', help='Optional path for storing backups')
    parser.add_argument('--verbose', action='store_true', help='Include MATCH and WORSE results in the output')
    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    backup_root = args.backup_dir or os.path.join(folder, 'temp_backup')
    redownload_dir = os.path.join(folder, 'temp_download')
    if args.redownload and not args.dry_run:
        os.makedirs(redownload_dir, exist_ok=True)

    itag_rankings = get_master_format_rankings()
    seen_ids = set()

    with open(args.output, 'w', encoding='utf-8') as out:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if not os.path.isfile(filepath):
                continue

            yt_id, file_itag = extract_info_from_filename(filename)
            if not yt_id or not file_itag or yt_id in seen_ids:
                continue
            seen_ids.add(yt_id)

            best_itag = get_best_live_itag(yt_id)
            if best_itag is None:
                print(f"[ERROR] Could not determine best itag for {yt_id}. Skipping.")
                continue

            file_rank = itag_rankings.get(file_itag)
            best_rank = itag_rankings.get(best_itag)

            if file_itag == best_itag:
                status = "MATCH"
                redownload = False
            elif file_rank is None or best_rank is None:
                status = "UNKNOWN"
                redownload = False
            else:
                if file_rank == best_rank:
                    status = "MATCH"
                    redownload = False
                elif best_rank < file_rank: # e.g 22 < 24 (22 is better)
                    status = "BETTER"
                    redownload = True
                else:
                    status = "WORSE"
                    redownload = False

            if args.verbose or status not in ("MATCH", "WORSE"):
                report_line = f"{filename}: File Itag: {file_itag} (Rank {file_rank}), Best Itag: {best_itag} (Rank {best_rank}) - {status}\n"
                out.write(report_line)
                print(report_line.strip())

            if redownload and args.redownload:
                perform_redownload(args, yt_id, folder, backup_root, redownload_dir, args.dry_run)

    if not args.dry_run and os.path.exists(redownload_dir) and not os.listdir(redownload_dir):
        os.rmdir(redownload_dir)
    print("\n[INFO] Process completed.")

if __name__ == "__main__":
    main()
