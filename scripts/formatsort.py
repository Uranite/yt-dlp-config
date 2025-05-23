from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube import _video

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

def print_format_list(formats_list):
    print("yt-dlp formats from _formats (sorted):") # Bottom is best
    for fmt in formats_list:
        print(f"itag={fmt.get('format_id')}, ext={fmt.get('ext')}, height={fmt.get('height')}, "
              f"fps={fmt.get('fps')}, vcodec={fmt.get('vcodec')}, acodec={fmt.get('acodec')}, "
              f"abr={fmt.get('abr')}, tbr={fmt.get('tbr')}, format_note={fmt.get('format_note')}")

print_format_list(info_dict['formats'])
