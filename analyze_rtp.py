import struct

def parse_rtp_packet(packet_hex):
    packet_bytes = bytes.fromhex(packet_hex.replace(' ', '').replace('\n', ''))
    
    if len(packet_bytes) < 12:
        print("Error: Packet too short (< 12 bytes)")
        return
    
    header = packet_bytes[:12]
    payload = packet_bytes[12:]
    
    byte0, byte1, seq, timestamp, ssrc = struct.unpack('!BBHII', header)
    
    version = (byte0 >> 6) & 0x03
    padding = (byte0 >> 5) & 0x01
    extension = (byte0 >> 4) & 0x01
    csrc_count = byte0 & 0x0F
    
    marker = (byte1 >> 7) & 0x01
    payload_type = byte1 & 0x7F
    
    print("=" * 60)
    print("RTP PACKET ANALYSIS")
    print("=" * 60)
    print(f"\nHeader (12 bytes):")
    print(f"  Raw: {header.hex(' ')}")
    print(f"\nVersion (V): {version}")
    print(f"Padding (P): {padding}")
    print(f"Extension (X): {extension}")
    print(f"CSRC Count (CC): {csrc_count}")
    print(f"Marker (M): {marker} {'(Last packet of frame)' if marker else ''}")
    print(f"Payload Type (PT): {payload_type} {'(JPEG)' if payload_type == 26 else ''}")
    print(f"Sequence Number: {seq}")
    print(f"Timestamp: {timestamp} (0x{timestamp:08X})")
    print(f"  -> Time: {timestamp/90000:.3f}s (at 90kHz clock)")
    print(f"SSRC: {ssrc} (0x{ssrc:08X})")
    print(f"\nPayload: {len(payload)} bytes")
    print(f"  First 32 bytes: {payload[:32].hex(' ')}")
    print(f"\nTotal packet size: {len(packet_bytes)} bytes")
    print("=" * 60)

def analyze_rtp_stream():
    print("RTP Packet Analyzer")
    print("=" * 60)
    print("\nPaste RTP packet in hexadecimal format (or 'q' to quit):")
    print("Example: 80 9A 00 01 00 00 0B B8 12 34 56 78 ...")
    print()
    
    while True:
        try:
            user_input = input("\nPacket hex: ").strip()
            
            if user_input.lower() == 'q':
                break
            
            if not user_input:
                continue
            
            parse_rtp_packet(user_input)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        packet_hex = ' '.join(sys.argv[1:])
        parse_rtp_packet(packet_hex)
    else:
        analyze_rtp_stream()
