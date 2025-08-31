import argparse
import json
import os
import shlex
import shutil
from datetime import datetime

import yt_dlp
from yt_dlp import YoutubeDL, parse_options
from yt_dlp.extractor.youtube import _video

class Logger:
    def __init__(self):
        self.warnings = []

    def debug(self, msg):
        if not msg.startswith('[debug] '):
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        self.warnings.append(msg)
        print(f"[Warning]: {msg}")

    def error(self, msg):
        print(f"[Error]: {msg}")

def extract_info_from_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data.get('_type') != 'video':
            return None

        video_id = data.get('id')
        format_id = data.get('format_id')
        vbr = data.get('vbr')

        if video_id and format_id:
            video_format_itag = format_id.split('+')[0]
            return video_id, video_format_itag, vbr
    except Exception as e:
        print(f"[ERROR] Failed to parse {json_path}: {e}")

    return None

def get_master_format_rankings():
    formats = _video.YoutubeIE._formats
    formats_list = []
    for itag, fmt in formats.items():
        fmt = fmt.copy()
        fmt['format_id'] = itag
        if 'url' not in fmt:
            fmt['url'] = f'https://dummy/{itag}'
        formats_list.append(fmt)

    info_dict = {'formats': formats_list}

    ydl = YoutubeDL(params={})
    ydl.sort_formats(info_dict)

    itag_rank_map = {}
    current_rank = 1
    for fmt in reversed(info_dict['formats']):  # Best to worst
        itag = fmt['format_id']
        itag_rank_map[itag] = current_rank
        current_rank += 1

    itag_rank_map['616'] = 0
    return itag_rank_map

def get_best_live_format(conf_args, youtube_id, max_retries=5):
    url = f"https://www.youtube.com/watch?v={youtube_id}"

    for attempt in range(1, max_retries + 1):
        logger = Logger()
        parsed = parse_options(conf_args)
        ydl_opts = parsed.ydl_opts
        # print("YDL OPTS:", ydl_opts)

        ydl_opts['quiet'] = True
        ydl_opts['logger'] = logger
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info['formats']
                best_format = formats[-1]  # Get the best format

            if logger.warnings:
                # print(f"[Attempt {attempt}] Warning detected, retrying...")
                continue

            return best_format['format_id'], best_format.get('vbr')
        except Exception as e:
            print(f"[Attempt {attempt}] Error: {e}")
            continue

    print("Failed to get a format without warnings.")
    return None, None

def move_files(src_folder, dest_folder, video_id):
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
    return moved

def find_downloaded_files(folder, video_id):
    files = os.listdir(folder)
    return [f for f in files if video_id in f]

def parse_yt_dlp_conf(config_path):
    args_list = []
    with open(config_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            args_list.extend(shlex.split(line))
    return args_list

def perform_redownload(conf_args, yt_id, folder, backup_root, redownload_dir, dry_run, max_retries=5):
    if not dry_run:
        os.makedirs(redownload_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(backup_root, f"{yt_id}_{timestamp}")

    print(f"\n[INFO] Redownloading {yt_id}, backing up to {backup_dir}")

    if dry_run:
        return

    moved_files = move_files(folder, backup_dir, yt_id)
    if not moved_files:
        print(f"[WARN] No files found to back up for {yt_id}. Skipping.")
        return

    # print("CONF ARGS:", conf_args)
    success = False

    for attempt in range(1, max_retries + 1):
        # Even if there is an error, yt-dlp can still download some/all the files, just different format
        for f in os.listdir(redownload_dir):
            try:
                os.remove(os.path.join(redownload_dir, f))
            except Exception as e:
                print(f"[WARN] Failed to clean up {f}: {e}")

        logger = Logger()
        parsed = parse_options(conf_args)
        ydl_opts = parsed.ydl_opts
        # print("YDL OPTS:", ydl_opts)

        ydl_opts['quiet'] = True
        ydl_opts['logger'] = logger
        ydl_opts['paths'] = {'home': redownload_dir}

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={yt_id}"])

            if logger.warnings:
                print(f"[Attempt {attempt}] Warning detected, retrying...")
                continue

            downloaded_files = find_downloaded_files(redownload_dir, yt_id)
            if not downloaded_files:
                print(f"[Attempt {attempt}] No files downloaded, retrying...")
                continue

            success = True
            break

        except Exception as e:
            print(f"[Attempt {attempt}] yt-dlp error: {e}")
            continue

    if not success:
        print(f"[ERROR] All {max_retries} download attempts failed for {yt_id}. Backup preserved at: {backup_dir}")
        return

    downloaded_files = find_downloaded_files(redownload_dir, yt_id)
    for f in downloaded_files:
        shutil.move(os.path.join(redownload_dir, f), os.path.join(folder, f))

    for f in os.listdir(redownload_dir):
        os.remove(os.path.join(redownload_dir, f))

def get_redownload_status(strategy, file_itag, best_itag, file_rank, best_rank, file_vbr, best_vbr):
    if file_rank is None or best_rank is None:
        return "UNKNOWN_RANK", False

    if strategy in ['better_format', 'better_format_vbr', 'better_format_vbr_diff']:
        if best_rank < file_rank:
            return f"BETTER_FORMAT ({file_itag} -> {best_itag})", True
        if best_rank > file_rank:
            return "WORSE_FORMAT", False
        if strategy == 'better_format_vbr' and best_vbr > file_vbr:
            return f"BETTER_VBR ({file_vbr}kbps -> {best_vbr}kbps)", True
        if strategy == 'better_format_vbr_diff' and best_vbr != file_vbr:
            return f"DIFFERENT_VBR ({file_vbr}kbps vs {best_vbr}kbps)", True
        return "MATCH", False

    if strategy == 'mismatch':
        if file_itag != best_itag:
            return f"FORMAT_MISMATCH ({file_itag} vs {best_itag})", True
        return "MATCH", False

    if strategy == 'mismatch_vbr_diff':
        if file_itag != best_itag:
            return f"FORMAT_MISMATCH ({file_itag} vs {best_itag})", True
        if best_vbr != file_vbr:
            return f"VBR_MISMATCH ({file_vbr}kbps vs {best_vbr}kbps)", True
        return "MATCH", False
    
    return "MATCH", False

def main():
    parser = argparse.ArgumentParser(description="Compare and redownload YouTube videos based on format and/or VBR")
    parser.add_argument('-f', '--folder', required=True,
                        help='Directory containing downloaded videos and their .info.json files')
    parser.add_argument('-l', '--log',
                        help='Log file path for saving comparison results')
    parser.add_argument('--log-auto', action='store_true',
                        help='Automatically determine log file location in the input folder')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without making any changes to files')
    parser.add_argument('--config', default='yt-dlp.conf',
                        help='Custom yt-dlp configuration file path')
    parser.add_argument('--backup-dir',
                        help='Custom directory for storing backups of original files')
    parser.add_argument('--verbose', action='store_true',
                        help='Show all comparison results, including matches')
    parser.add_argument('--strategy',
                        choices=['better_format', 'better_format_vbr',
                                 'better_format_vbr_diff', 'mismatch', 'mismatch_vbr_diff'],
                        default='better_format',
                        help='''
                        Redownload strategy:
                        - better_format: Redownload if the live format is better (default).
                        - better_format_vbr: Like better_format, but also checks VBR if formats match.
                        - better_format_vbr_diff: Like better_format, but redownloads if VBR differs, regardless of which is better.
                        - mismatch: Redownload if the format doesn't match the live formats.
                        - mismatch_vbr_diff: Like mismatch, but if the format matches, redownloads if VBR differs, regardless of which is better.
                        ''')
    parser.add_argument('--process-format', nargs='+',
                        help='Only process videos with these format IDs (e.g., 399 400 401)')

    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    args.config = os.path.abspath(args.config)
    backup_root = args.backup_dir or os.path.join(folder, 'temp_backup')
    redownload_dir = os.path.join(folder, 'temp_download')

    conf_args = parse_yt_dlp_conf(args.config)
    log_file = os.path.join(folder, 'itagcompare.log') if args.log_auto else args.log

    itag_rankings = get_master_format_rankings()
    seen_ids = set()

    out_file = None
    if log_file:
        out_file = open(log_file, 'w', encoding='utf-8')
        print(f"[INFO] Logging to {log_file}")

    try:
        for filename in os.listdir(folder):
            if not filename.endswith('.info.json'):
                continue

            json_path = os.path.join(folder, filename)
            json_info = extract_info_from_json(json_path)
            
            if not json_info:
                continue
            
            yt_id, file_itag, file_vbr = json_info
            
            if yt_id in seen_ids:
                continue
            seen_ids.add(yt_id)

            if args.process_format and file_itag not in args.process_format:
                if args.verbose:
                    print(f"[SKIP] {filename}: Format {file_itag} not in filter list")
                continue

            best_itag, best_vbr = get_best_live_format(conf_args, yt_id)
            if best_itag is None:
                print(f"[ERROR] Could not determine best format for {yt_id}. Skipping.")
                continue

            file_rank = itag_rankings.get(file_itag)
            best_rank = itag_rankings.get(best_itag)

            status, redownload = get_redownload_status(
                args.strategy, file_itag, best_itag, file_rank, best_rank, file_vbr, best_vbr
            )

            # ANSI color codes
            GREEN = '\033[92m'
            BLUE = '\033[94m'
            YELLOW = '\033[93m'
            END = '\033[0m'

            if redownload or args.verbose:
                file_itag_colored = f"{GREEN}{file_itag}{END}"
                file_rank_colored = f"{BLUE}{file_rank}{END}" if file_rank is not None else "N/A"
                best_itag_colored = f"{GREEN}{best_itag}{END}"
                best_rank_colored = f"{BLUE}{best_rank}{END}" if best_rank is not None else "N/A"
                status_colored = f"{YELLOW}{status}{END}" if redownload else status

                report_line_colored = (
                    f"{filename}: File Itag: {file_itag_colored} (Rank {file_rank_colored}), "
                    f"Best Itag: {best_itag_colored} (Rank {best_rank_colored}) - {status_colored}"
                )
                print(report_line_colored)

                if out_file is not None:
                    report_line = (
                        f"{filename}: File Itag: {file_itag} (Rank {file_rank}), "
                        f"Best Itag: {best_itag} (Rank {best_rank}) - {status}"
                    )
                    out_file.write(report_line + '\n')

            if redownload:
                perform_redownload(conf_args, yt_id, folder, backup_root, redownload_dir, args.dry_run)

    finally:
        if not args.dry_run:
            if os.path.exists(redownload_dir) and not os.listdir(redownload_dir):
                os.rmdir(redownload_dir)
        if out_file is not None:
            out_file.close()
            print(f"[INFO] Log saved to {log_file}")
        print("\n[INFO] Process completed.")

if __name__ == "__main__":
    main()
