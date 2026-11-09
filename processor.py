import cv2
import os
import numpy as np
from scenedetect import detect, ContentDetector
from ultralytics import YOLO
from moviepy.editor import VideoFileClip, concatenate_videoclips

def process_video(video_path, output_dir, progress_callback):
    results = {}
    
    model = YOLO('yolov8n.pt')
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    progress_callback(10)
    
    # 1. Scene Boundaries
    scene_list = detect(video_path, ContentDetector())
    scene_boundaries = [(scene[0].get_seconds(), scene[1].get_seconds()) for scene in scene_list]
    results['scenes'] = scene_boundaries
    
    fgbg = cv2.createBackgroundSubtractorMOG2()
    
    motion_map_path = os.path.join(output_dir, 'motion_map.png')
    tracked_video_path = os.path.join(output_dir, 'tracked_output.mp4')
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_tracked = cv2.VideoWriter(tracked_video_path, fourcc, fps, (width, height))
    
    motion_accumulator = np.zeros((height, width), dtype=np.float32)
    
    important_frames_dir = os.path.join(output_dir, 'important_frames')
    os.makedirs(important_frames_dir, exist_ok=True)
    
    important_frame_paths = []
    
    # Process frames (skipped logic for optimization on 60 min videos)
    frame_skip = max(1, int(fps)) # Process 1 frame per second to avoid timeout
    
    frame_idx = 0
    saved_frames = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_idx += 1
        if frame_idx % 100 == 0:
            progress = 10 + int((frame_idx / total_frames) * 70)
            progress_callback(progress)
            
        fgmask = fgbg.apply(frame)
        motion_accumulator += (fgmask > 200).astype(np.float32)
        
        if frame_idx % frame_skip == 0:
            results_yolo = model(frame, classes=[0], verbose=False) # 0 is person
            annotated_frame = results_yolo[0].plot()
            out_tracked.write(annotated_frame)
            
            if np.mean(fgmask) > 10.0 and saved_frames < 20:
                frame_filename = f"keyframe_{frame_idx}.jpg"
                cv2.imwrite(os.path.join(important_frames_dir, frame_filename), frame)
                important_frame_paths.append(f"important_frames/{frame_filename}")
                saved_frames += 1
                
    cap.release()
    out_tracked.release()
    
    motion_map_normalized = cv2.normalize(motion_accumulator, None, 0, 255, cv2.NORM_MINMAX)
    motion_map_color = cv2.applyColorMap(motion_map_normalized.astype(np.uint8), cv2.COLORMAP_HOT)
    cv2.imwrite(motion_map_path, motion_map_color)
    
    progress_callback(85)
    
    try:
        clip = VideoFileClip(video_path)
        clips = []
        for start, end in scene_boundaries[:10]: # Limit summary to first 10 scenes
            duration = min(2.0, end - start)
            clips.append(clip.subclip(start, start + duration))
        
        if clips:
            summary_clip = concatenate_videoclips(clips)
            summary_path = os.path.join(output_dir, 'summary.mp4')
            summary_clip.write_videofile(summary_path, codec="libx264", audio_codec="aac", fps=fps)
            results['summary'] = 'summary.mp4'
    except Exception as e:
        pass
        
    progress_callback(95)
    
    results['motion_map'] = 'motion_map.png'
    results['tracked_video'] = 'tracked_output.mp4'
    results['important_frames'] = important_frame_paths
    
    return results
