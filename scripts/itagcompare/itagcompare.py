import os
import re
import shutil
import argparse
import subprocess
from datetime import datetime
import yt_dlp
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube import _video
import json

class Logger:
    def __init__(self):
        self.warnings = []

    def debug(self, msg):
        pass

    def warning(self, msg):
        self.warnings.append(msg)
        # print(f"[Warning]: {msg}")

    def error(self, msg):
        print(f"[Error]: {msg}")

def extract_info_from_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        video_id = data['id']
        format_id = data['format_id']
        vbr = data['vbr']

        base_name = os.path.basename(json_path)[:-10]  # Remove .info.json

        if video_id and format_id and base_name:
            video_format_itag = format_id.split('+')[0]
            return video_id, video_format_itag, base_name, vbr
    except Exception as e:
        print(f"[ERROR] Failed to parse {json_path}: {e}")

    return None, None, None, None

def get_master_format_rankings():
    formats = _video.YoutubeIE._formats
    formats_list = []
    for itag, fmt in formats.items():
        fmt = fmt.copy()
        fmt['format_id'] = str(itag)
        if 'url' not in fmt:
            fmt['url'] = f'https://dummy/{itag}'
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

def get_best_live_format(youtube_id, max_retries=5):
    url = f"https://www.youtube.com/watch?v={youtube_id}"

    for attempt in range(1, max_retries + 1):
        logger = Logger()
        ydl_opts = {
            'quiet': True,
            'logger': logger
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info['formats']
                best_format = formats[-1]  # Get the best format

            if logger.warnings:
                # print(f"[Attempt {attempt}] Warning detected, retrying...")
                continue

            return best_format['format_id'], best_format['vbr']
        except Exception as e:
            print(f"[Attempt {attempt}] Error: {e}")
            continue

    print("Failed to get a format without warnings.")
    return None, None

def move_files(src_folder, dest_folder, video_id, base_name, use_base_name_fallback=False):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    moved = []
    files = os.listdir(src_folder)
    
    for filename in files:
        if video_id in filename:
            src = os.path.join(src_folder, filename)
            dest = os.path.join(dest_folder, filename)
            shutil.move(src, dest)
            moved.append(filename)
    
    if not moved and use_base_name_fallback and base_name:
        for filename in files:
            if base_name in filename:
                src = os.path.join(src_folder, filename)
                dest = os.path.join(dest_folder, filename)
                shutil.move(src, dest)
                moved.append(filename)
    
    return moved

def find_downloaded_files(folder, video_id, base_name, use_base_name_fallback=False):
    files = os.listdir(folder)
    matched = [f for f in files if video_id in f]
    if not matched and use_base_name_fallback and base_name:
        matched = [f for f in files if base_name in f]
    return matched

def perform_redownload(args, yt_id, title, folder, backup_root, redownload_dir, dry_run, max_retries=5):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(backup_root, f"{yt_id}_{timestamp}")

    print(f"\n[INFO] Redownloading {yt_id}, backing up to {backup_dir}")

    if dry_run:
        return

    moved_files = move_files(folder, backup_dir, yt_id, title, args.use_title_matching)
    if not moved_files:
        print(f"[WARN] No files found to back up for {yt_id}. Skipping.")
        return

    for attempt in range(1, max_retries + 1):
        logger = Logger()
        ydl_opts = {
            'quiet': True,
            'logger': logger,
            'paths': {'home': redownload_dir},
            'config_locations': [args.config] if args.config else None
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={yt_id}"])

            if logger.warnings:
                # print(f"[Attempt {attempt}] Warning detected, retrying...")
                continue

            break
        except Exception as e:
            print(f"[Attempt {attempt}] yt-dlp error: {e}")
            continue

    downloaded_files = find_downloaded_files(redownload_dir, yt_id, title, args.use_title_matching)
    if not downloaded_files:
        print(f"[ERROR] Redownload failed for {yt_id}. Backup preserved at: {backup_dir}")
        return

    for f in downloaded_files:
        shutil.move(os.path.join(redownload_dir, f), os.path.join(folder, f))

    for f in os.listdir(redownload_dir):
        os.remove(os.path.join(redownload_dir, f))

def main():
    parser = argparse.ArgumentParser(description="Compare and redownload YouTube videos based on .info.json metadata.")
    parser.add_argument('-f', '--folder', required=True, 
                      help='Directory containing downloaded videos and their .info.json files')
    parser.add_argument('-o', '--output', required=True, 
                      help='Output file path for saving comparison results')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Run without making any changes to files')
    parser.add_argument('--config', default='yt-dlp.conf', 
                      help='Custom yt-dlp configuration file path')
    parser.add_argument('--backup-dir', 
                      help='Custom directory for storing backups of original files')
    parser.add_argument('--verbose', action='store_true', 
                      help='Show all comparison results, including matches')
    # I didn't test this
    parser.add_argument('--use-title-matching', action='store_true', 
                      help='Match files by title when video ID is not found in filename')
    
    strategy_group = parser.add_mutually_exclusive_group()
    strategy_group.add_argument('--strategy', 
                              choices=['better_format', 'better_format_vbr', 'better_format_vbr_diff', 'redownload_if_mismatch', 'redownload_if_mismatch_vbr_diff', 'redownload_if_match'],
                              default='better_format',
                              help='''
                              Redownload strategy:
                              - better_format: redownload if live format is better (default)
                              - better_format_vbr: like better_format but also checks VBR if formats match
                              - better_format_vbr_diff: like better_format but redownloads if VBR is different, regardless of which is better
                              - redownload_if_mismatch: redownload if format doesn't match live formats
                              - redownload_if_mismatch_vbr_diff: like redownload_if_mismatch but also checks VBR if formats match
                              - redownload_if_match: redownload if local format matches best available format
                              ''')
    
    parser.add_argument('--filter-format', nargs='+', 
                      help='Only process videos with these format IDs (e.g., 401 402 303)')
    
    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    backup_root = args.backup_dir or os.path.join(folder, 'temp_backup')
    redownload_dir = os.path.join(folder, 'temp_download')
    if not args.dry_run:
        os.makedirs(redownload_dir, exist_ok=True)

    itag_rankings = get_master_format_rankings()
    seen_ids = set()

    with open(args.output, 'w', encoding='utf-8') as out:
        for filename in os.listdir(folder):
            if not filename.endswith('.info.json'):
                continue

            json_path = os.path.join(folder, filename)
            yt_id, file_itag, title, file_vbr = extract_info_from_json(json_path)
            if not yt_id or not file_itag or yt_id in seen_ids:
                continue
            seen_ids.add(yt_id)

            if args.filter_format and file_itag not in args.filter_format:
                if args.verbose:
                    print(f"[SKIP] {filename}: Format {file_itag} not in filter list")
                continue
                
            best_itag, best_vbr = get_best_live_format(yt_id)
            if best_itag is None:
                print(f"[ERROR] Could not determine best format for {yt_id}. Skipping.")
                continue
                
            file_rank = itag_rankings.get(file_itag)
            best_rank = itag_rankings.get(best_itag)
            
            if args.strategy == 'better_format':
                if file_itag == best_itag:
                    status = "MATCH"
                    redownload = False
                elif file_rank is None or best_rank is None:
                    status = "UNKNOWN"
                    redownload = False
                else:
                    if best_rank < file_rank:  # Lower rank is better
                        status = f"BETTER_FORMAT ({file_itag} -> {best_itag})"
                        redownload = True
                    else:
                        status = "WORSE"
                        redownload = False
                        
            elif args.strategy == 'better_format_vbr':
                if file_itag == best_itag:
                    if best_vbr is not None and file_vbr is not None:
                        if best_vbr > file_vbr:
                            status = f"BETTER_VBR ({file_vbr} -> {best_vbr}kbps)"
                            redownload = True
                        else:
                            status = "SAME_VBR"
                            redownload = False
                    else:
                        status = "MATCH (VBR not available)"
                        redownload = False
                elif file_rank is None or best_rank is None:
                    status = "UNKNOWN"
                    redownload = False
                else:
                    if best_rank < file_rank:
                        status = f"BETTER_FORMAT ({file_itag} -> {best_itag})"
                        redownload = True
                    else:
                        status = "WORSE"
                        redownload = False
                        
            elif args.strategy == 'redownload_if_mismatch':
                if file_itag != best_itag:
                    status = f"FORMAT_MISMATCH (Current: {file_itag}, Best: {best_itag})"
                    redownload = True
                else:
                    status = "FORMAT_MATCH"
                    redownload = False
                        
            elif args.strategy == 'better_format_vbr_diff':
                if file_itag == best_itag:
                    if best_vbr is not None and file_vbr is not None:
                        if best_vbr != file_vbr:
                            status = f"DIFFERENT_VBR (Current: {file_vbr}kbps, Live: {best_vbr}kbps)"
                            redownload = True
                        else:
                            status = "SAME_VBR"
                            redownload = False
                    else:
                        status = "MATCH (VBR not available)"
                        redownload = False
                elif file_rank is None or best_rank is None:
                    status = "UNKNOWN"
                    redownload = False
                else:
                    if best_rank < file_rank:  # Lower rank is better
                        status = f"BETTER_FORMAT ({file_itag} -> {best_itag})"
                        redownload = True
                    else:
                        status = "WORSE"
                        redownload = False
                        
            elif args.strategy == 'redownload_if_mismatch_vbr_diff':
                if file_itag != best_itag:
                    status = f"FORMAT_MISMATCH (Current: {file_itag}, Best: {best_itag})"
                    redownload = True
                else:
                    if best_vbr is not None and file_vbr is not None:
                        if best_vbr != file_vbr:
                            status = f"FORMAT_MATCH_VBR_MISMATCH (Current: {file_vbr}kbps, Live: {best_vbr}kbps)"
                            redownload = True
                        else:
                            status = "FORMAT_MATCH_VBR_MATCH"
                            redownload = False
                    else:
                        status = "FORMAT_MATCH (VBR not available)"
                        redownload = False
                        
            elif args.strategy == 'redownload_if_match':
                if file_itag == best_itag:
                    status = "FORMAT_MATCH"
                    redownload = True
                else:
                    status = f"FORMAT_MISMATCH (Current: {file_itag}, Best: {best_itag})"
                    redownload = False

            VISIBLE_STATUSES = {
                "BETTER_FORMAT",
                "BETTER_VBR",
                "FORMAT_MISMATCH",
                "CHECK_FAILED",
                "UNKNOWN",
                "DIFFERENT_VBR",
                "FORMAT_MATCH_VBR_MISMATCH",
            }

            if args.verbose or any(status.startswith(s) for s in VISIBLE_STATUSES):
                report_line = f"{filename}: File Itag: {file_itag} (Rank {file_rank}), Best Itag: {best_itag} (Rank {best_rank}) - {status}\n"
                out.write(report_line)
                print(report_line.strip())

            if redownload and not args.dry_run:
                perform_redownload(args, yt_id, title, folder, backup_root, redownload_dir, args.dry_run)

    if not args.dry_run:
        if os.path.exists(redownload_dir) and not os.listdir(redownload_dir):
            os.rmdir(redownload_dir)
    print("\n[INFO] Process completed.")

if __name__ == "__main__":
    main()
