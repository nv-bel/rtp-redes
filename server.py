import socket
import cv2
import struct
import time
import random
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

RTP_VERSION = 2
PAYLOAD_TYPE = 26
MTU_SIZE = 1400
RTP_HEADER_SIZE = 12
MAX_PAYLOAD_SIZE = MTU_SIZE - RTP_HEADER_SIZE
CLOCK_RATE = 90000
DSCP_EF = 0xB8

AES_KEY = b'0123456789abcdef0123456789abcdef'

class RTPServer:
    def __init__(self, video_path, host='127.0.0.1', port=5004):
        self.video_path = video_path
        self.host = host
        self.port = port
        self.sequence_number = 0
        self.timestamp = 0
        self.ssrc = random.randint(0, 0xFFFFFFFF)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, DSCP_EF)
            print(f"QoS: DSCP EF (0x{DSCP_EF:02X}) configured")
        except Exception as e:
            print(f"Warning: Could not set DSCP: {e}")
        
        self.aesgcm = AESGCM(AES_KEY)
        print(f"Server initialized - SSRC: {self.ssrc}")
        print(f"Target: {host}:{port}")
    
    def create_rtp_header(self, marker=0):
        byte0 = (RTP_VERSION << 6) | 0
        byte1 = (marker << 7) | PAYLOAD_TYPE
        
        header = struct.pack('!BBHII',
            byte0,
            byte1,
            self.sequence_number & 0xFFFF,
            self.timestamp & 0xFFFFFFFF,
            self.ssrc
        )
        return header
    
    def encrypt_payload(self, payload, header):
        nonce = struct.pack('!Q', self.sequence_number) + b'\x00\x00\x00\x00'
        encrypted = self.aesgcm.encrypt(nonce, payload, header)
        return encrypted
    
    def send_frame(self, frame_data):
        num_chunks = (len(frame_data) + MAX_PAYLOAD_SIZE - 1) // MAX_PAYLOAD_SIZE
        
        for i in range(num_chunks):
            start = i * MAX_PAYLOAD_SIZE
            end = min(start + MAX_PAYLOAD_SIZE, len(frame_data))
            chunk = frame_data[start:end]
            
            marker = 1 if i == num_chunks - 1 else 0
            header = self.create_rtp_header(marker)
            
            encrypted_payload = self.encrypt_payload(chunk, header)
            
            packet = header + encrypted_payload
            self.sock.sendto(packet, (self.host, self.port))
            
            self.sequence_number += 1
        
        return num_chunks
    
    def stream_video(self):
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {self.video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30
        
        frame_duration = 1.0 / fps
        timestamp_increment = int(CLOCK_RATE / fps)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Video: {self.video_path}")
        print(f"FPS: {fps}, Total frames: {total_frames}")
        print(f"Timestamp increment: {timestamp_increment} (90kHz clock)")
        print("\nStreaming started... Press Ctrl+C to stop\n")
        
        frame_count = 0
        total_packets = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("\nEnd of video, restarting...")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.timestamp = 0
                    frame_count = 0
                    continue
                
                start_time = time.time()
                
                ret, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    continue
                
                jpeg_bytes = jpeg_data.tobytes()
                
                num_packets = self.send_frame(jpeg_bytes)
                total_packets += num_packets
                
                frame_count += 1
                self.timestamp += timestamp_increment
                
                if frame_count % 30 == 0:
                    print(f"Frame {frame_count}/{total_frames} | "
                          f"Seq: {self.sequence_number} | "
                          f"TS: {self.timestamp} | "
                          f"Size: {len(jpeg_bytes)} bytes | "
                          f"Packets: {num_packets}")
                
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_duration - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\n\nStreaming stopped")
            print(f"Total frames sent: {frame_count}")
            print(f"Total packets sent: {total_packets}")
        finally:
            cap.release()
            self.sock.close()

if __name__ == "__main__":
    import sys
    
    video_file = "video.mp4"
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
    
    server = RTPServer(video_file)
    server.stream_video()
