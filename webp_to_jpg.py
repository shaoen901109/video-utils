import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("尚未安裝 Pillow 套件，請先在終端機執行: pip install Pillow")
    sys.exit(1)

def convert_to_jpg(webp_path: Path, output_path: Path):
    try:
        with Image.open(webp_path) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            # 以最高品質 100 儲存
            im.save(output_path, "JPEG", quality=100)
            print(f"成功: {webp_path.name} -> {output_path.name}")
    except Exception as e:
        print(f"轉換失敗 {webp_path.name}: {e}")

def process_file(file_path: Path):
    if file_path.suffix.lower() != ".webp":
        print(f"略過非 webp 檔案: {file_path.name}")
        return
    
    # 輸出檔放在原本資料夾中
    output_path = file_path.with_suffix(".jpg")
    convert_to_jpg(file_path, output_path)

def process_directory(dir_path: Path):
    # 建立命名加上 '_jpg' 字尾的資料夾
    output_dir = dir_path.parent / f"{dir_path.name}_jpg"
    output_dir.mkdir(exist_ok=True)
    
    # 掃描資料夾內所有的 .webp 檔案 (不分大小寫)
    webp_files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() == '.webp']
    
    if not webp_files:
        print(f"資料夾中沒有找到 .webp 檔案: {dir_path}")
        return
    
    print(f"在 {dir_path.name} 找到 {len(webp_files)} 個 webp 檔案，準備轉換...")
    for webp_file in webp_files:
        output_path = output_dir / f"{webp_file.stem}.jpg"
        convert_to_jpg(webp_file, output_path)
    print(f"資料夾轉換完成，輸出至: {output_dir}")

def main():
    print("========== WebP 轉 JPG 工具 ==========")
    print("可自動判斷輸入為單一檔案或資料夾。")
    print("輸入 q 離開程式。")
    print("======================================")
    
    while True:
        try:
            user_input = input("\n請貼上 webp 檔案或資料夾路徑: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n程式結束")
            break
            
        if user_input.lower() == 'q':
            print("程式結束")
            break
            
        if not user_input:
            continue
            
        # 移除前後可能含有的引號 (雙引號或單引號)
        user_input = user_input.strip('"\'')
        path = Path(user_input)
        
        processed = False
        
        # 1. 檢查是否為資料夾
        if path.is_dir():
            process_directory(path)
            processed = True
            
        # 2. 檢查是否為直接指向的檔案
        if path.is_file():
            process_file(path)
            processed = True
        # 3. 如果路徑無副檔名，且不是直接的檔案，嘗試補上 .webp
        elif path.suffix == '':
            webp_path = path.with_suffix('.webp')
            if webp_path.is_file():
                process_file(webp_path)
                processed = True
                
        if not processed:
            print(f"找不到有效的文件或資料夾: {user_input}")

if __name__ == '__main__':
    main()
