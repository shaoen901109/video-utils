import os
import sys
import subprocess
import shutil

def check_dependencies():
    """檢查是否已安裝 ffmpeg 與 ffprobe"""
    if not shutil.which("ffmpeg"):
        print("錯誤: 找不到 ffmpeg。請先安裝 FFmpeg 並將其加入系統環境變數 PATH 中。")
        sys.exit(1)
    if not shutil.which("ffprobe"):
        print("錯誤: 找不到 ffprobe。請確認 FFmpeg 安裝完整。")
        sys.exit(1)

def get_video_dimensions(filepath):
    """取得影片的原始寬高"""
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', filepath]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, startupinfo=startupinfo)
        w, h = result.stdout.strip().split('x')
        return int(w), int(h)
    except Exception as e:
        print(f"無法獲取影片尺寸: {e}")
        return None, None

def get_video_duration(filepath):
    """取得影片總長度(秒)"""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, startupinfo=startupinfo)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def has_audio(filepath):
    """檢查影片是否有聲音軌"""
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', filepath]
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, startupinfo=startupinfo)
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

def time_to_sec(t_str):
    """將 HH:MM:SS 或 MM:SS 轉換為秒數"""
    parts = t_str.strip().split(':')
    sec = 0.0
    for p in parts:
        sec = sec * 60 + float(p)
    return sec

def main():
    check_dependencies()
    print("=== 影片旋轉工具 (支援保留原影片片段合併) ===")
    
    # 第一步：影片路徑
    raw_path = input("1. 請貼上影片路徑 (僅限 mp4 格式): ").strip()
    raw_path = raw_path.strip('\'"')
    
    if not raw_path.lower().endswith('.mp4'):
        raw_path += '.mp4'
        
    if not os.path.exists(raw_path):
        print(f"錯誤: 找不到檔案 {raw_path}")
        return

    # 第二步：旋轉角度
    print("\n2. 請選擇順時針旋轉角度:")
    print("[1] 90度")
    print("[2] 180度")
    print("[3] 270度")
    angle_choice = input("請輸入選項編號 [預設: 1]: ").strip()
    
    vf_filters = []
    degree_str = "90"
    if angle_choice == '2':
        vf_filters.append("transpose=1,transpose=1")
        degree_str = "180"
    elif angle_choice == '3':
        vf_filters.append("transpose=2")
        degree_str = "270"
    else:
        vf_filters.append("transpose=1")
        degree_str = "90"

    # 第三步：是否只旋轉部分片段
    is_partial_input = input("\n3. 是否只旋轉部分片段，其餘片段維持正常？ [y/N] (預設空白為 N): ").strip().upper()
    is_partial = (is_partial_input == 'Y')

    start_sec = 0.0
    end_sec = 0.0

    if is_partial:
        # 第四步：時分秒
        time_range = input("4. 請輸入要旋轉片段的時分秒 (例如 00:00:00~00:20:20): ").strip()
        try:
            start_str, end_str = time_range.split('~')
            start_sec = time_to_sec(start_str)
            end_sec = time_to_sec(end_str)
        except ValueError:
            print("錯誤: 時間格式不正確，請確保包含 '~' 符號區隔開始與結束時間。")
            return
            
        # 第五步：裁切填滿 or 保留黑邊
        print("\n5. 旋轉片段後，該片段要如何處理以匹配原影片比例？")
        print("[1] 裁切填滿 (Crop to fill)")
        print("[2] 保留黑邊 (Pad with black bars)")
        fit_choice = input("請輸入選項編號 [預設: 2]: ").strip()
        fit_mode = 'crop' if fit_choice == '1' else 'pad'

        # 確保片段能完美接回原影片，對於90/270度需修正長寬
        if degree_str in ["90", "270"]:
            orig_w, orig_h = get_video_dimensions(raw_path)
            if orig_w and orig_h:
                if fit_mode == 'pad':
                    vf_filters.append(f"scale={orig_w}:{orig_h}:force_original_aspect_ratio=decrease")
                    vf_filters.append(f"pad={orig_w}:{orig_h}:(ow-iw)/2:(oh-ih)/2")
                elif fit_mode == 'crop':
                    vf_filters.append(f"scale={orig_w}:{orig_h}:force_original_aspect_ratio=increase")
                    vf_filters.append(f"crop={orig_w}:{orig_h}")
    else:
        pass
        
    dir_name = os.path.dirname(raw_path)
    base_name = os.path.basename(raw_path)
    name, ext = os.path.splitext(base_name)
    output_name = f"{name}_旋轉{degree_str}度{ext}"
    output_path = os.path.join(dir_name, output_name)

    if is_partial:
        dur = get_video_duration(raw_path)
        if dur <= 0:
            print("錯誤: 無法讀取影片長度。")
            return
        
        if end_sec > dur:
            end_sec = dur
            
        if start_sec >= end_sec:
            print("錯誤: 開始時間必須早於結束時間。")
            return
            
        audio_exists = has_audio(raw_path)
        
        parts = 0
        filter_strs = []
        concat_v = ""
        concat_a = ""
        
        # 第一段：原影片 (開頭 ~ 旋轉前)
        if start_sec > 0:
            parts += 1
            filter_strs.append(f"[0:v]trim=0:{start_sec},setpts=PTS-STARTPTS[v{parts}]")
            concat_v += f"[v{parts}]"
            if audio_exists:
                filter_strs.append(f"[0:a]atrim=0:{start_sec},asetpts=PTS-STARTPTS[a{parts}]")
                concat_a += f"[a{parts}]"
                
        # 第二段：旋轉片段
        parts += 1
        v_part2 = f"[0:v]trim={start_sec}:{end_sec},setpts=PTS-STARTPTS"
        if vf_filters:
            v_part2 += "," + ",".join(vf_filters)
        v_part2 += f"[v{parts}]"
        filter_strs.append(v_part2)
        concat_v += f"[v{parts}]"
        if audio_exists:
            filter_strs.append(f"[0:a]atrim={start_sec}:{end_sec},asetpts=PTS-STARTPTS[a{parts}]")
            concat_a += f"[a{parts}]"
            
        # 第三段：原影片 (旋轉後 ~ 結尾)
        if end_sec < dur:
            parts += 1
            filter_strs.append(f"[0:v]trim={end_sec}:{dur},setpts=PTS-STARTPTS[v{parts}]")
            concat_v += f"[v{parts}]"
            if audio_exists:
                filter_strs.append(f"[0:a]atrim={end_sec}:{dur},asetpts=PTS-STARTPTS[a{parts}]")
                concat_a += f"[a{parts}]"
                
        # 合併所有片段
        concat_filter = concat_v
        if audio_exists:
            concat_filter += f"{concat_a}concat=n={parts}:v=1:a=1[outv][outa]"
        else:
            concat_filter += f"concat=n={parts}:v=1:a=0[outv]"
        filter_strs.append(concat_filter)
        
        filter_complex = ";".join(filter_strs)
        
        cmd = ['ffmpeg', '-y', '-i', raw_path, '-filter_complex', filter_complex, '-map', '[outv]']
        if audio_exists:
            cmd.extend(['-map', '[outa]'])
            
        # 設定輸出編碼 (因拼接濾鏡需重編碼，配置 H.264 以維持相容性)
        cmd.extend(['-c:v', 'libx264', '-crf', '23', '-preset', 'fast'])
        if audio_exists:
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        cmd.append(output_path)
        
    else:
        # 單純旋轉整部影片 (不需 filter_complex，僅套用畫面濾鏡)
        cmd = ['ffmpeg', '-y', '-i', raw_path, '-vf', ",".join(vf_filters), '-c:v', 'libx264', '-crf', '23', '-preset', 'fast', '-c:a', 'copy', output_path]

    print("\n--- 開始處理影片 ---")
    print(f"執行指令: {' '.join(cmd)}")
    if is_partial:
        print("注意：因為包含影片的精準分割、旋轉與重新合併，這需要重新編碼，處理時間可能會較長，請耐心等候。")
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        subprocess.run(cmd, check=True, startupinfo=startupinfo)
        print(f"\n✅ 處理完成！\n輸出檔案已儲存至: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 影片處理失敗: 執行 FFmpeg 時發生錯誤 (代碼 {e.returncode})")
    except KeyboardInterrupt:
        print("\n⚠️ 使用者中斷執行。")

if __name__ == "__main__":
    main()
