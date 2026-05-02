from scapy.all import sniff, IP, TCP, UDP, ICMP
import time
import threading

captured_packets = []
lock = threading.Lock()

def get_protocol(packet):
    if TCP in packet:
        return "TCP"
    elif UDP in packet:
        return "UDP"
    elif ICMP in packet:
        return "ICMP"
    return "OTHER"

def packet_callback(packet):
    if IP in packet:
        info = {
            "timestamp": time.time(),
            "src": packet[IP].src,
            "dst": packet[IP].dst,
            "protocol": get_protocol(packet),
            "size": len(packet)
        }
        with lock:
            captured_packets.append(info)

def start_capture(interface="Wi-Fi"):
    thread = threading.Thread(
        target=lambda: sniff(iface=interface, prn=packet_callback, store=False),
        daemon=True
    )
    thread.start()