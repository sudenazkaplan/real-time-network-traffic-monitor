import time
from capture import captured_packets, lock

def get_stats(window_seconds=1):
    now = time.time()
    cutoff = now - window_seconds

    with lock:
        recent = [p for p in captured_packets if p["timestamp"] > cutoff]
        # Belleği temizle — 60 saniyeden eski paketleri at
        captured_packets[:] = [p for p in captured_packets if p["timestamp"] > now - 60]

    if not recent:
        return empty_stats()

    total_bytes = sum(p["size"] for p in recent)
    proto_counts = {"TCP": 0, "UDP": 0, "ICMP": 0, "OTHER": 0}
    talkers = {}

    for p in recent:
        proto_counts[p["protocol"]] += 1
        ip = p["src"]
        if ip not in talkers:
            talkers[ip] = {"ip": ip, "bytes": 0, "protocol": p["protocol"]}
        talkers[ip]["bytes"] += p["size"]

    top_talkers = sorted(talkers.values(), key=lambda x: x["bytes"], reverse=True)[:5]

    return {
        "bytes_per_sec": total_bytes,
        "mbps": round(total_bytes * 8 / 1_000_000, 2),
        "pps": len(recent),
        "protocol_dist": proto_counts,
        "top_talkers": top_talkers,
        "active_hosts": len(talkers)
    }

def empty_stats():
    return {
        "bytes_per_sec": 0, "mbps": 0, "pps": 0,
        "protocol_dist": {"TCP": 0, "UDP": 0, "ICMP": 0, "OTHER": 0},
        "top_talkers": [], "active_hosts": 0
    }