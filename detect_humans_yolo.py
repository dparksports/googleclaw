import os
import csv
from ultralytics import YOLO
import torch

def find_videos(root_dir, target_folder_name):
    video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv')
    found_videos = []
    for root, dirs, files in os.walk(root_dir):
        if target_folder_name.lower() in root.lower():
            for file in files:
                if file.lower().endswith(video_exts):
                    found_videos.append(os.path.join(root, file))
    return found_videos

def main():
    search_root = r'C:\Users\honey'
    target_folder = 'FileHistory'
    output_csv = 'human_detection_events.csv'
    
    print("Searching for videos in FileHistory...")
    videos = find_videos(search_root, target_folder)
    
    if not videos:
        print("No video files found in FileHistory directories.")
        return

    print(f"Found {len(videos)} videos. Initializing YOLO...")
    # Using yolo11n.pt (latest version from Ultralytics)
    model = YOLO('yolo11n.pt')
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Running on device: {device}")

    results_list = []

    for vid_path in videos:
        print(f"Processing: {vid_path}")
        try:
            # classes=[0] targets 'person' in COCO dataset
            # stream=True processes video frame by frame to save memory
            results = model.predict(source=vid_path, conf=0.45, classes=[0], device=device, stream=True)
            
            for frame_idx, r in enumerate(results):
                for box in r.boxes:
                    results_list.append({
                        'file_path': vid_path,
                        'frame': frame_idx,
                        'confidence': round(float(box.conf[0]), 4),
                        'bbox': [round(x, 2) for x in box.xyxy[0].tolist()]
                    })
        except Exception as e:
            print(f"Error processing {vid_path}: {e}")

    # Saving to CSV
    if results_list:
        keys = results_list[0].keys()
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(results_list)
        print(f"Detection complete. CSV saved to: {output_csv}")
    else:
        print("No humans detected in the scanned videos.")

if __name__ == '__main__':
    main()