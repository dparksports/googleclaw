import os
import csv
import torch
from ultralytics import YOLO

def find_videos(root_dir):
    video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv')
    found_videos = []
    print(f"[*] Searching for videos in: {root_dir}")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(video_exts):
                found_videos.append(os.path.join(root, file))
    
    # Sort by modification time (most recent first)
    found_videos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return found_videos

def main():
    # 1. Dynamic Pathing
    home = os.path.expanduser("~")
    search_root = os.path.join(home, "Downloads", "reolink")
    output_csv = 'human_detection_events.csv'
    
    if not os.path.exists(search_root):
        print(f"[!] Error: Directory not found: {search_root}")
        return

    # 2. GPU Detection
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[*] Using device: {device.upper()}")
    
    try:
        model = YOLO('yolov8n.pt')  # Downloads if missing
    except Exception as e:
        print(f"[!] Model error: {e}")
        return

    videos = find_videos(search_root)
    print(f"[*] Found {len(videos)} videos.")

    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Video Path', 'Frame', 'Confidence', 'Timestamp'])

        for video in videos:
            # 3. Informing the User
            print(f"  > Processing: {os.path.basename(video)}")
            
            results = model.track(source=video, conf=0.5, classes=[0], device=device, stream=True, verbose=False)
            
            for result in results:
                if result.boxes:
                    for box in result.boxes:
                        conf = float(box.conf[0])
                        writer.writerow([video, "N/A", f"{conf:.2f}", "Event Detected"])
    
    print(f"[*] Detection complete. Results saved to {output_csv}")

if __name__ == "__main__":
    main()
