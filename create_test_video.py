import cv2
import numpy as np

def create_test_video(filename='video.mp4', duration=10, fps=30, width=640, height=480):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    print(f"Creating test video: {filename}")
    print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")
    print(f"Total frames: {total_frames}")
    
    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        hue = int((i / total_frames) * 180)
        frame[:, :] = [hue, 255, 255]
        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
        
        text = f"Frame {i+1}/{total_frames}"
        cv2.putText(frame, text, (50, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        time_text = f"Time: {i/fps:.2f}s"
        cv2.putText(frame, time_text, (50, height//2 + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
        
        if (i + 1) % fps == 0:
            print(f"Progress: {(i+1)/total_frames*100:.1f}%")
    
    out.release()
    print(f"\nTest video created successfully: {filename}")

if __name__ == "__main__":
    import sys
    
    duration = 10
    if len(sys.argv) > 1:
        duration = int(sys.argv[1])
    
    create_test_video(duration=duration)
