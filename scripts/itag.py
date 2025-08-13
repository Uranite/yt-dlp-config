import yt_dlp
import argparse

def list_formats(url, best_only=False):
    ydl_opts = {'quiet': True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info['formats']

        if best_only:
            best = formats[-1]
            print(f"Best format for: {info['title']}\n")
            print(f"itag: {best.get('format_id')}, ext: {best.get('ext')}, resolution: {best.get('resolution')}, "
                  f"fps: {best.get('fps')}, vcodec: {best.get('vcodec')}, acodec: {best.get('acodec')}, "
                  f"note: {best.get('format_note')}")
        else:
            print(f"Available formats for: {info['title']}\n")
            for fmt in formats:
                print(f"itag: {fmt.get('format_id')}, ext: {fmt.get('ext')}, resolution: {fmt.get('resolution')}, "
                      f"fps: {fmt.get('fps')}, vcodec: {fmt.get('vcodec')}, acodec: {fmt.get('acodec')}, "
                      f"note: {fmt.get('format_note')}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List YouTube format IDs using yt-dlp')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--best', action='store_true', help='Only show the best (bottommost) format')

    args = parser.parse_args()
    list_formats(args.url, best_only=args.best)
