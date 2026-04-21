import os
import csv
import torch
import time
from ultralytics import YOLO

def find_videos(root_dir):
    video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv')
    found_videos = []
    print(f"[*] Scanning directory: {root_dir}")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(video_exts):
                found_videos.append(os.path.join(root, file))
    
    # Sort by modification time (most recent first)
    found_videos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return found_videos

def main():
    # Configuration
    home = os.path.expanduser("~")
    search_root = os.path.join(home, "Downloads", "reolink")
    output_csv = 'filehistory_human_events.csv'
    
    # OPTIMIZATION: vid_stride=5 skips 4 out of 5 frames (5x speedup)
    # conf=0.4 is a good balance for security footage
    STRIDE = 5 
    CONFIDENCE = 0.4
    
    if not os.path.exists(search_root):
        print(f"[!] Error: Target directory does not exist: {search_root}")
        return

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[*] Hardware: {torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU'}")
    
    try:
        model = YOLO('yolo11n.pt') 
        if device == 'cuda':
            model.to(device)
    except Exception as e:
        print(f"[!] Error loading model: {e}")
        return

    videos = find_videos(search_root)
    total_videos = len(videos)
    if total_videos == 0:
        print("[!] No videos found to process.")
        return

    print(f"[*] Found {total_videos} videos. Starting High-Speed Detection (Stride={STRIDE})...")

    start_time = time.time()
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Video Path', 'Object', 'Confidence', 'Status', 'Timestamp'])

        for idx, video in enumerate(videos, 1):
            filename = os.path.basename(video)
            progress = (idx / total_videos) * 100
            print(f"[{progress:.1f}%] ({idx}/{total_videos}) Processing: {filename}")
            
            try:
                # OPTIMIZATION: vid_stride for speed, half=True for RTX 4090 Tensor Core usage
                results = model.predict(
                    source=video, 
                    conf=CONFIDENCE, 
                    classes=[0], 
                    device=device, 
                    stream=True, 
                    verbose=False,
                    vid_stride=STRIDE,
                    half=(device == 'cuda')
                )
                
                human_detected = False
                for result in results:
                    if result.boxes:
                        for box in result.boxes:
                            conf = float(box.conf[0])
                            # Approximate timestamp based on stride and fps (simplified)
                            writer.writerow([video, "person", f"{conf:.2f}", "Detected", time.ctime(os.path.getmtime(video))])
                            human_detected = True
                        if human_detected: break # For security logs, one detection per file is often enough

                if not human_detected:
                    writer.writerow([video, "person", "0.00", "No Detection", time.ctime(os.path.getmtime(video))])

            except Exception as e:
                print(f"    [!] Error: {e}")
                writer.writerow([video, "N/A", "0.00", f"Error: {e}", "N/A"])
    
    elapsed = time.time() - start_time
    print(f"\n[*] Finished {total_videos} files in {elapsed:.1f}s ({elapsed/total_videos:.2f}s per file).")
    print(f"[*] Report generated: {output_csv}")

if __name__ == "__main__":
    main()
