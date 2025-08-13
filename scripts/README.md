# yt-dlp Scripts

This directory contains utility scripts for yt-dlp.

## Scripts

### 1. extract.py
Extracts YouTube video IDs from filenames in a specified folder and saves them to a file.

**Usage:**
```bash
python extract.py -f <input_folder> -o <output_file>
```

**Example:**
```bash
python extract.py -f ./videos -o youtube_ids.txt
```

### 2. formatsort.py
Lists all available yt-dlp formats sorted by quality (best at the bottom).

**Usage:**
```bash
python formatsort.py
```

### 3. itag.py
Lists available formats for a YouTube video.

**Usage:**
```bash
python itag.py <youtube_url> [--best]
```

**Options:**
- `--best` - Only show the best available format

**Example:**
```bash
python itag.py https://youtu.be/tzD9OxAHtzU --best
```

### 4. itagcompare/
A more advanced script for comparing and managing downloaded video formats.

#### itagcompare.py
Compares downloaded video formats and can redownload videos in better quality if available.

**Usage:**
```bash
python itagcompare.py [options]
```

**Options:**
- Run `python itagcompare.py -h` to check the options.

**Example:**
```bash
python itagcompare.py --folder .\downloads --log-auto
```

### 5. sort.py
Sorts YouTube video IDs in a file.

**Usage:**
```bash
python sort.py <input_file>
```

**Example:**
```bash
python sort.py youtube_ids.txt
```

### 6. updateytdlp.bat
Batch script to update yt-dlp to the latest pre-release version.

**Usage:**
Double-click the file or run from command prompt.

## Dependencies

- Python 3.9+ or later
- yt-dlp

## License

This project is licensed under the terms of the MIT license.
