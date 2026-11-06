# video-utils

English | [繁體中文](README.zh-TW.md)

Three small, independent, interactive Python scripts for video and image processing. Each script is standalone; run it and answer the prompts (the prompts are in Traditional Chinese).

## Scripts

### `rotate_video.py`
Rotates an `.mp4` clockwise by 90, 180 or 270 degrees. Optionally rotate only a time range (`HH:MM:SS~HH:MM:SS`) and keep the rest untouched; the rotated part can be cropped to fill or padded with black bars to match the original frame size. Output is re-encoded with H.264 (CRF 23) and saved next to the input as `<name>_旋轉<angle>度.mp4`.

```
python rotate_video.py
```

### `timelapse_maker.py`
Builds time-lapse videos from a folder of numbered photos (`.jpg`, `.jpeg`, `.png`). It detects consecutive number sequences, lets you pick a number range (e.g. `0032~0078`), then renders one video per combination of the options you choose:

- frame rate: 18, 24, 29.97, 30, 59.94, 60 or custom
- size: 1080 (16:9), 1080 (9:16), 2.7K, 4K, original or custom (center-crop then resize)
- mode: plain time-lapse, accumulate (lighten / star trails), or accumulate over a fixed number of recent frames

Output is H.264 / yuv420p MP4. You are asked for the output folder (default: `timelapse_output` inside the photo folder).

```
python timelapse_maker.py
```

### `webp_to_jpg.py`
Converts `.webp` to `.jpg` (quality 100). Paste a single file path (the JPG is saved next to it) or a folder path (JPGs go to a sibling folder named `<folder>_jpg`). Enter `q` to quit.

```
python webp_to_jpg.py
```

## Requirements

- Python 3 (tested on Windows)
- Python packages: `pip install -r requirements.txt` (`rotate_video.py` needs none; `webp_to_jpg.py` needs Pillow; `timelapse_maker.py` needs opencv-python and numpy).
- [FFmpeg](https://ffmpeg.org/download.html) (`ffmpeg` and `ffprobe` on your `PATH`) for `rotate_video.py` and `timelapse_maker.py`.

## Credits

| Purpose | Component | License |
|---|---|---|
| Video rotation and encoding (external program) | [FFmpeg / ffprobe](https://ffmpeg.org/) | LGPL-2.1+ or GPL-2+, depends on the build |
| Frame processing | [opencv-python](https://github.com/opencv/opencv-python) | Apache-2.0 |
| Array math | [NumPy](https://numpy.org/) | BSD-3-Clause |
| Image conversion | [Pillow](https://python-pillow.org/) | HPND |

Developed with the help of [Claude Code](https://claude.com/claude-code) (Anthropic).

## Author

- Website: https://shaoenstudio.com
- Email: shaoenstudio@gmail.com
- GitHub: [@shaoen901109](https://github.com/shaoen901109)

## License

MIT, see [LICENSE](LICENSE).
