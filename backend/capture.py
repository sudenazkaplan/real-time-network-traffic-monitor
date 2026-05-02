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
    def _sniff():
        try:
            sniff(iface=interface, prn=packet_callback, store=False)
        except Exception as e:
            print(f"[!] Capture failed ({e}) — running in demo mode")

    thread = threading.Thread(target=_sniff, daemon=True)
    thread.start()
    print(f"[+] Capture started on {interface}")