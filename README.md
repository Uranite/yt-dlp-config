# yt-dlp Config for Archival

Configuration files for [yt-dlp](https://github.com/yt-dlp/yt-dlp) to archive YouTube channels and playlists with (hopefully) optimal settings for long-term preservation.

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.9 or later
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- (Optional) [aria2c](https://aria2.github.io/) for potentially faster downloads

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Uranite/yt-dlp-config.git
   cd yt-dlp-config
   ```

2. Install yt-dlp (nightly):
   ```bash
   pip install -U --pre "yt-dlp[default]"
   ```

## Quick Start

### For Channel Archival
1. Add channel URLs to `channel/channels.txt` (one URL per line)
2. Run the download script:
   ```bash
   cd channel
   .\dl.bat
   ```

### For Playlist Archival
1. Add playlist URLs to `playlist/playlists.txt` (one URL per line)
2. Run the download script:
   ```bash
   cd playlist
   .\dl.bat
   ```

## Customization

### Adding More Channels/Playlists
- Edit the respective `channels.txt` or `playlists.txt` file
- Add one URL per line

### Modifying Download Behavior
Edit the `yt-dlp.conf` file in either the `channel/` or `playlist/` directory to change download settings. Refer to the [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#usage-and-options) for available options.

## Updating

To update yt-dlp to the latest nightly version, run:

```bash
pip install -U --pre "yt-dlp[default]"
```

Or use the included update script:

```bash
.\scripts\updateytdlp.bat
```

## License

This project is licensed under the terms of the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
