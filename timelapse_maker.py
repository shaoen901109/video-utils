import os
import cv2
import numpy as np
import subprocess
import glob
import re
import sys
from collections import deque

# ─── 圖片 I/O ────────────────────────────────────────────────────────────────

def imread_unicode(path):
    """以 numpy fromfile 讀取含非 ASCII 字元路徑的圖片。"""
    try:
        return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"讀取圖片失敗: {path}, 錯誤: {e}")
        return None

def get_images_in_folder(folder_path):
    """掃描資料夾內支援的圖片，回傳去重複後排序的清單。"""
    exts = ['.jpg', '.jpeg', '.png']
    found = set()
    for ext in exts:
        for f in glob.glob(os.path.join(folder_path, f'*{ext}')):
            found.add(os.path.normpath(f))          # normpath 統一路徑分隔符
        for f in glob.glob(os.path.join(folder_path, f'*{ext.upper()}')):
            found.add(os.path.normpath(f))
    return sorted(found)                             # 排序後回傳，不含重複

# ─── 序列分析 ─────────────────────────────────────────────────────────────────

def parse_filename(filename):
    """解析檔名，回傳 (prefix, num_str, suffix)；找不到數字時回傳 (None, None, None)。"""
    basename = os.path.basename(filename)
    match = re.search(r'(.*?)(\d+)(\.[^.]+)$', basename)
    if match:
        return match.groups()
    return None, None, None

def find_sequences(images):
    """將圖片依連續編號分組，回傳 [[seq1], [seq2], ...]。"""
    sequences = []
    current_seq = []
    last_prefix = last_suffix = None
    last_num = None

    for img in images:
        prefix, num_str, suffix = parse_filename(img)
        if not num_str:
            continue

        num = int(num_str)
        same_prefix = (last_prefix == prefix and last_suffix == suffix)
        consecutive   = (last_num is not None and num == last_num + 1)

        if same_prefix and consecutive:
            current_seq.append(img)
        else:
            if current_seq:
                sequences.append(current_seq)
            current_seq = [img]

        last_prefix, last_suffix, last_num = prefix, suffix, num

    if current_seq:
        sequences.append(current_seq)

    return sequences

# ─── 影格裁切縮放 ─────────────────────────────────────────────────────────────

def get_frame_crop_resize(img, target_w, target_h):
    """置中裁切後縮放至目標尺寸；target=0 時回傳原尺寸。"""
    if target_w == 0 and target_h == 0:
        return img

    h, w = img.shape[:2]
    target_ar = target_w / target_h
    source_ar = w / h

    if source_ar > target_ar:
        new_w = int(h * target_ar)
        start_x = (w - new_w) // 2
        cropped = img[:, start_x:start_x + new_w]
    elif source_ar < target_ar:
        new_h = int(w / target_ar)
        start_y = (h - new_h) // 2
        cropped = img[start_y:start_y + new_h, :]
    else:
        cropped = img

    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)

# ─── FFmpeg 寫入器 ────────────────────────────────────────────────────────────

def open_ffmpeg_writer(out_path, frame_w, frame_h, fps):
    """
    開啟 FFmpeg 子程序，以 pipe stdin 接收 rawvideo(BGR24)，
    輸出 H.264 / yuv420p MP4，相容 Windows 媒體播放器。
    """
    # 分數幀率對應（避免浮點字串精度問題）
    fps_map = {29.97: '30000/1001', 59.94: '60000/1001'}
    fps_str = fps_map.get(fps, str(int(fps) if fps == int(fps) else fps))

    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{frame_w}x{frame_h}',
        '-pix_fmt', 'bgr24',
        '-r', fps_str,
        '-i', 'pipe:0',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',   # 確保 Windows 相容性
        out_path
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def write_ffmpeg_frame(proc, frame):
    proc.stdin.write(frame.tobytes())

def close_ffmpeg_writer(proc):
    proc.stdin.close()
    proc.wait()

# ─── 主程式 ───────────────────────────────────────────────────────────────────

def main():
    print("=== 星空縮時攝影與疊加製片工具 ===")

    # ── 步驟 1：輸入資料夾 ──────────────────────────────────────────────────
    folder_path = input("1. 請輸入照片所在的資料夾路徑 (可直接貼上): ").strip('"').strip("'").strip()
    if not os.path.isdir(folder_path):
        print("找不到該資料夾！")
        return

    images = get_images_in_folder(folder_path)
    if not images:
        print("資料夾中找不到支援的照片檔案 (.jpg / .jpeg / .png)")
        return

    # ── 步驟 2：掃描序列並選取範圍 ─────────────────────────────────────────
    sequences = find_sequences(images)
    print("\n掃描到以下照片序列:")
    if not sequences:
        print("找不到連續編號的照片序列。")
        return

    for i, seq in enumerate(sequences):
        start_name = os.path.basename(seq[0])
        end_name   = os.path.basename(seq[-1])
        _, start_num_str, _ = parse_filename(start_name)
        _, end_num_str,   _ = parse_filename(end_name)
        prefix, _, _         = parse_filename(start_name)
        label = f"{prefix}{start_num_str}~{end_num_str}" if len(seq) > 1 else start_name
        print(f"  [{i+1}] {label}  (共 {len(seq)} 張)")

    range_input = input("\n2. 請輸入要製作的照片編號範圍 (例如 '0032~0078'): ").strip()
    m = re.search(r'(\d+)\s*~\s*(\d+)', range_input)
    if not m:
        print("輸入格式錯誤，需為 '開始編號~結束編號' 格式。")
        return

    start_num_input = int(m.group(1))
    end_num_input   = int(m.group(2))

    selected_images = [
        img for img in images
        if (lambda ns: ns is not None and start_num_input <= int(ns) <= end_num_input)(parse_filename(img)[1])
    ]

    if not selected_images:
        print("找不到符合該編號範圍的照片。")
        return

    print(f"-> 成功選取 {len(selected_images)} 張照片。")

    # ── 步驟 3：幀率 ────────────────────────────────────────────────────────
    fps_options = {'1': 18, '2': 24, '3': 29.97, '4': 30, '5': 59.94, '6': 60}
    print("\n3. 請選擇幀率(fps):")
    print("[1]18  [2]24  [3]29.97  [4]30  [5]59.94  [6]60  [0]自訂")
    fps_input = input("請輸入數字選擇(可多選空白分隔，例如 '1 2'，輸入0自訂): ").strip()

    selected_fps_list = []
    tokens = fps_input.split()
    if '0' in tokens:
        try:
            custom_fps = float(input("請輸入自訂幀率 (例如 15): "))
            selected_fps_list.append(custom_fps)
        except Exception:
            print("無效輸入，忽略自訂幀率。")
    for t in tokens:
        if t in fps_options:
            v = fps_options[t]
            if v not in selected_fps_list:
                selected_fps_list.append(v)
    if not selected_fps_list:
        print("未選擇有效幀率，預設使用 30 fps。")
        selected_fps_list = [30]

    # ── 步驟 4：畫質 ────────────────────────────────────────────────────────
    quality_options = {
        '1': ('1080(16:9)',  1920, 1080),
        '2': ('1080(9:16)', 1080, 1920),
        '3': ('2.7K(16:9)', 2560, 1440),
        '4': ('4K(16:9)',   3840, 2160),
        '5': ('原始',          0,    0),
    }
    print("\n4. 請選擇畫質:")
    print("[1]1080(16:9)  [2]1080(9:16)  [3]2.7K(16:9)  [4]4K(16:9)  [5]原始  [0]自訂")
    quality_input = input("請輸入數字選擇(可多選空白分隔，例如 '1 4'，輸入0自訂): ").strip()

    selected_qualities = []
    q_tokens = quality_input.split()
    if '0' in q_tokens:
        try:
            cust_w = int(input("請輸入自訂寬度 (pixel): "))
            cust_h = int(input("請輸入自訂高度 (pixel): "))
            selected_qualities.append((f'自訂({cust_w}x{cust_h})', cust_w, cust_h))
        except Exception:
            print("無效輸入，忽略自訂畫質。")
    for t in q_tokens:
        if t in quality_options and quality_options[t] not in selected_qualities:
            selected_qualities.append(quality_options[t])
    if not selected_qualities:
        print("未選擇有效畫質，預設使用 1080(16:9)。")
        selected_qualities = [quality_options['1']]

    # ── 步驟 5：模式 ────────────────────────────────────────────────────────
    mode_options = {'1': '純縮時', '2': '疊加', '3': '疊加固定長度'}
    print("\n5. 請選擇影片模式:")
    print("[1]純縮時  [2]疊加  [3]疊加固定長度")
    mode_input = input("請輸入數字選擇(可多選空白分隔，例如 '1 2 3'): ").strip()

    selected_modes = []
    tail_length = 15
    for t in mode_input.split():
        if t in mode_options and mode_options[t] not in selected_modes:
            selected_modes.append(mode_options[t])
    if not selected_modes:
        print("未選擇有效模式，預設使用 純縮時。")
        selected_modes = ['純縮時']
    if '疊加固定長度' in selected_modes:
        try:
            tail_length = int(input("你選擇了'疊加固定長度'，請輸入要保留的照片數量 (預設 15): ") or 15)
        except Exception:
            print("輸入無效，預設保留 15 張。")
            tail_length = 15

    # ── 步驟 6：確認 ────────────────────────────────────────────────────────
    default_out = os.path.join(folder_path, "timelapse_output")
    output_dir = input(f"輸出資料夾路徑 [預設: {default_out}]: ").strip().strip('"').strip("'").strip() or default_out
    jobs = []
    for fps in selected_fps_list:
        for q_name, q_w, q_h in selected_qualities:
            for mode in selected_modes:
                jobs.append({'fps': fps, 'q_name': q_name, 'q_w': q_w,
                              'q_h': q_h, 'mode': mode, 'tail': tail_length})

    print(f"\n=== 6. 最後確認 ===")
    print(f"總共將製作 {len(jobs)} 部影片：")
    for j in jobs:
        print(f"  - {j['mode']} | {j['q_name']} | {j['fps']} fps")
    print(f"\n輸出路徑: {output_dir}")
    input("按 Enter 鍵開始製作...")

    # ── 輸出 ────────────────────────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)

    for job_idx, job in enumerate(jobs):
        fps   = job['fps']
        q_w   = job['q_w']
        q_h   = job['q_h']
        mode  = job['mode']
        q_name_safe = job['q_name'].replace(':', '_').replace('/', '_')
        fps_label   = str(int(fps)) if fps == int(fps) else str(fps)

        print(f"\n[進度 {job_idx+1}/{len(jobs)}] 製作: {mode} | {job['q_name']} | {fps} fps")

        base_filename = f"{mode}_{q_name_safe}_{fps_label}fps_{job_idx+1}"
        out_filename = f"{base_filename}.mp4"
        out_path = os.path.join(output_dir, out_filename)
        
        counter = 2
        while os.path.exists(out_path):
            out_filename = f"{base_filename} ({counter}).mp4"
            out_path = os.path.join(output_dir, out_filename)

        # 決定實際輸出尺寸（原始畫質需讀第一張）
        if q_w == 0 and q_h == 0:
            first_img = imread_unicode(selected_images[0])
            if first_img is None:
                print("無法讀取第一張照片，略過此影片。")
                continue
            frame_h, frame_w = first_img.shape[:2]
        else:
            frame_w, frame_h = q_w, q_h

        # 開啟 FFmpeg 寫入器
        proc = open_ffmpeg_writer(out_path, frame_w, frame_h, fps)

        accumulator = None
        frame_queue = deque(maxlen=job['tail'] if mode == '疊加固定長度' else None)
        total = len(selected_images)

        for idx, img_path in enumerate(selected_images):
            sys.stdout.write(f"\r  處理中... {idx+1}/{total} ({(idx+1)/total*100:.1f}%)")
            sys.stdout.flush()

            img = imread_unicode(img_path)
            if img is None:
                continue

            frame = get_frame_crop_resize(img, q_w, q_h)

            if mode == '純縮時':
                write_ffmpeg_frame(proc, frame)

            elif mode == '疊加':
                accumulator = frame.copy() if accumulator is None else np.maximum(accumulator, frame)
                write_ffmpeg_frame(proc, accumulator)

            elif mode == '疊加固定長度':
                frame_queue.append(frame.copy())
                acc = frame_queue[0].copy()
                for f in list(frame_queue)[1:]:
                    acc = np.maximum(acc, f)
                write_ffmpeg_frame(proc, acc)

        close_ffmpeg_writer(proc)
        print(f"\n  => 完成: {out_filename}")

    print("\n所有影片製作完畢！")
    try:
        os.startfile(output_dir)
    except Exception as e:
        print(f"無法自動開啟資料夾: {e}")

if __name__ == "__main__":
    main()
