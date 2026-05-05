import socket
import cv2
import struct
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from collections import deque
import numpy as np

RTP_HEADER_SIZE = 12
JITTER_BUFFER_SIZE = 10

AES_KEY = b'0123456789abcdef0123456789abcdef'

class RTPClient:
    def __init__(self, host='0.0.0.0', port=5004):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.sock.settimeout(5.0)
        
        self.aesgcm = AESGCM(AES_KEY)
        
        self.frame_buffer = []
        self.jitter_buffer = deque(maxlen=JITTER_BUFFER_SIZE)
        
        self.last_seq = None
        self.packets_received = 0
        self.packets_lost = 0
        self.last_timestamp = None
        self.jitter = 0.0
        self.last_arrival_time = None
        
        print(f"Client listening on {host}:{port}")
        print("Waiting for RTP packets...\n")
    
    def parse_rtp_header(self, data):
        if len(data) < RTP_HEADER_SIZE:
            return None
        
        header = data[:RTP_HEADER_SIZE]
        payload = data[RTP_HEADER_SIZE:]
        
        byte0, byte1, seq, timestamp, ssrc = struct.unpack('!BBHII', header)
        
        version = (byte0 >> 6) & 0x03
        marker = (byte1 >> 7) & 0x01
        payload_type = byte1 & 0x7F
        
        return {
            'version': version,
            'marker': marker,
            'payload_type': payload_type,
            'sequence': seq,
            'timestamp': timestamp,
            'ssrc': ssrc,
            'header': header,
            'payload': payload
        }
    
    def decrypt_payload(self, encrypted_payload, header, sequence):
        try:
            nonce = struct.pack('!Q', sequence) + b'\x00\x00\x00\x00'
            decrypted = self.aesgcm.decrypt(nonce, encrypted_payload, header)
            return decrypted
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def update_statistics(self, seq, timestamp):
        current_time = time.time()
        
        if self.last_seq is not None:
            expected_seq = (self.last_seq + 1) & 0xFFFF
            if seq != expected_seq:
                if seq > expected_seq:
                    lost = seq - expected_seq
                else:
                    lost = (0xFFFF - expected_seq) + seq + 1
                self.packets_lost += lost
        
        self.packets_received += 1
        self.last_seq = seq
        
        if self.last_timestamp is not None and self.last_arrival_time is not None:
            transit_time = current_time - self.last_arrival_time
            timestamp_diff = (timestamp - self.last_timestamp) / 90000.0
            
            d = abs(transit_time - timestamp_diff)
            self.jitter += (d - self.jitter) / 16.0
        
        self.last_timestamp = timestamp
        self.last_arrival_time = current_time
    
    def print_statistics(self):
        total_packets = self.packets_received + self.packets_lost
        loss_rate = (self.packets_lost / total_packets * 100) if total_packets > 0 else 0
        
        print(f"\n--- Statistics ---")
        print(f"Packets received: {self.packets_received}")
        print(f"Packets lost: {self.packets_lost}")
        print(f"Loss rate: {loss_rate:.2f}%")
        print(f"Jitter: {self.jitter*1000:.2f} ms")
        print("------------------\n")
    
    def receive_and_display(self):
        print("Starting video reception...\n")
        
        frame_count = 0
        stats_interval = 30
        
        try:
            while True:
                try:
                    data, addr = self.sock.recvfrom(65535)
                    
                    rtp_info = self.parse_rtp_header(data)
                    if not rtp_info:
                        continue
                    
                    decrypted_payload = self.decrypt_payload(
                        rtp_info['payload'],
                        rtp_info['header'],
                        rtp_info['sequence']
                    )
                    
                    if decrypted_payload is None:
                        continue
                    
                    self.update_statistics(rtp_info['sequence'], rtp_info['timestamp'])
                    
                    self.frame_buffer.append(decrypted_payload)
                    
                    if rtp_info['marker'] == 1:
                        frame_data = b''.join(self.frame_buffer)
                        self.frame_buffer = []
                        
                        try:
                            nparr = np.frombuffer(frame_data, np.uint8)
                            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if frame is not None:
                                frame_count += 1
                                
                                info_text = [
                                    f"Frame: {frame_count}",
                                    f"Seq: {rtp_info['sequence']}",
                                    f"TS: {rtp_info['timestamp']}",
                                    f"SSRC: {rtp_info['ssrc']}",
                                    f"Lost: {self.packets_lost}",
                                    f"Jitter: {self.jitter*1000:.1f}ms"
                                ]
                                
                                y_offset = 30
                                for i, text in enumerate(info_text):
                                    cv2.putText(frame, text, (10, y_offset + i*25),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                
                                cv2.imshow('RTP Video Stream', frame)
                                
                                if frame_count % stats_interval == 0:
                                    self.print_statistics()
                                
                                if cv2.waitKey(1) & 0xFF == ord('q'):
                                    break
                        except Exception as e:
                            print(f"Error decoding frame: {e}")
                
                except socket.timeout:
                    print("Timeout waiting for packets...")
                    continue
        
        except KeyboardInterrupt:
            print("\n\nClient stopped by user")
        finally:
            self.print_statistics()
            cv2.destroyAllWindows()
            self.sock.close()

if __name__ == "__main__":
    client = RTPClient()
    client.receive_and_display()
