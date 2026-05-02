import sqlite3
import time

DB_PATH = "netwatch.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS traffic_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            mbps REAL,
            pps INTEGER,
            active_hosts INTEGER,
            tcp_count INTEGER,
            udp_count INTEGER,
            icmp_count INTEGER,
            other_count INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS top_talkers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            ip TEXT,
            protocol TEXT,
            bytes INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_stats(stats):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pd = stats["protocol_dist"]
    c.execute('''
        INSERT INTO traffic_stats 
        (timestamp, mbps, pps, active_hosts, tcp_count, udp_count, icmp_count, other_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        time.time(),
        stats["mbps"],
        stats["pps"],
        stats["active_hosts"],
        pd.get("TCP", 0),
        pd.get("UDP", 0),
        pd.get("ICMP", 0),
        pd.get("OTHER", 0)
    ))
    for t in stats["top_talkers"]:
        c.execute('''
            INSERT INTO top_talkers (timestamp, ip, protocol, bytes)
            VALUES (?, ?, ?, ?)
        ''', (time.time(), t["ip"], t["protocol"], t["bytes"]))
    conn.commit()
    conn.close()

def get_history(minutes=60):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cutoff = time.time() - (minutes * 60)
    c.execute('''
        SELECT timestamp, mbps, pps, active_hosts,
               tcp_count, udp_count, icmp_count, other_count
        FROM traffic_stats
        WHERE timestamp > ?
        ORDER BY timestamp ASC
    ''', (cutoff,))
    rows = c.fetchall()
    conn.close()
    return rows

def cleanup_old_data(days=7):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cutoff = time.time() - (days * 86400)
    c.execute("DELETE FROM traffic_stats WHERE timestamp < ?", (cutoff,))
    c.execute("DELETE FROM top_talkers WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()