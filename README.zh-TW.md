# video-utils

[English](README.md) | 繁體中文

三支各自獨立的影音／圖片處理小腳本，執行後依照提示輸入即可（提示文字為繁體中文）。

## 腳本說明

### `rotate_video.py`
把 `.mp4` 影片順時針旋轉 90、180 或 270 度。可以只旋轉某段時間（格式 `HH:MM:SS~HH:MM:SS`），其餘片段維持原樣；旋轉後的片段可選「裁切填滿」或「保留黑邊」，以符合原影片尺寸。輸出以 H.264（CRF 23）重新編碼，存在原檔旁邊，檔名為 `<原檔名>_旋轉<角度>度.mp4`。

```
python rotate_video.py
```

### `timelapse_maker.py`
把資料夾內的編號照片（`.jpg`、`.jpeg`、`.png`）合成縮時影片。程式會偵測連續編號的序列，讓你輸入要用的編號範圍（例如 `0032~0078`），再依你選的選項組合各輸出一部影片：

- 幀率：18、24、29.97、30、59.94、60，或自訂
- 畫質：1080（16:9）、1080（9:16）、2.7K、4K、原始尺寸，或自訂（置中裁切後縮放）
- 模式：純縮時、疊加（取最亮，做星軌）、疊加固定長度（只疊最近 N 張）

輸出為 H.264 / yuv420p 的 MP4。輸出資料夾會詢問你（預設為照片資料夾內的 `timelapse_output`）。

```
python timelapse_maker.py
```

### `webp_to_jpg.py`
把 `.webp` 轉成 `.jpg`（品質 100）。貼上單一檔案路徑（JPG 存在原檔旁），或貼上資料夾路徑（JPG 存到同層的 `<資料夾名>_jpg` 資料夾）。輸入 `q` 離開。

```
python webp_to_jpg.py
```

## 需求

- Python 3（在 Windows 上測試）
- Python 套件：`pip install -r requirements.txt`（`rotate_video.py` 不需要額外套件；`webp_to_jpg.py` 需要 Pillow；`timelapse_maker.py` 需要 opencv-python、numpy）。
- [FFmpeg](https://ffmpeg.org/download.html)（`ffmpeg`、`ffprobe` 要在 `PATH` 內）：`rotate_video.py`、`timelapse_maker.py` 需要。

## 技術來源與致謝

| 用途 | 元件 | 授權 |
|---|---|---|
| 影片旋轉與編碼（外部程式） | [FFmpeg / ffprobe](https://ffmpeg.org/) | LGPL-2.1+ 或 GPL-2+，依建置版本 |
| 影格處理 | [opencv-python](https://github.com/opencv/opencv-python) | Apache-2.0 |
| 陣列運算 | [NumPy](https://numpy.org/) | BSD-3-Clause |
| 圖片轉檔 | [Pillow](https://python-pillow.org/) | HPND |

開發過程使用 [Claude Code](https://claude.com/claude-code)（Anthropic）協助。

## 作者

- 網站：https://shaoenstudio.com
- 聯絡信箱：shaoenstudio@gmail.com
- GitHub：[@shaoen901109](https://github.com/shaoen901109)

## 授權

MIT，見 [LICENSE](LICENSE)。
