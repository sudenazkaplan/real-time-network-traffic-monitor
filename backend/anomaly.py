import numpy as np
from collections import deque

class AnomalyDetector:
    def __init__(self, window=60):
        self.mbps_history = deque(maxlen=window)
        self.pps_history = deque(maxlen=window)
        self.threshold = 2.5  # z-score eşiği

    def add(self, mbps, pps):
        self.mbps_history.append(mbps)
        self.pps_history.append(pps)

    def check(self, mbps, pps):
        alerts = []

        if len(self.mbps_history) < 10:
            return alerts

        # Z-score hesapla
        mbps_mean = np.mean(self.mbps_history)
        mbps_std  = np.std(self.mbps_history) or 0.001
        pps_mean  = np.mean(self.pps_history)
        pps_std   = np.std(self.pps_history) or 0.001

        mbps_z = (mbps - mbps_mean) / mbps_std
        pps_z  = (pps  - pps_mean)  / pps_std

        if mbps_z > self.threshold:
            alerts.append({
                "type": "danger",
                "msg": f"Anormal bandwidth spike — {mbps} Mbps (z={mbps_z:.1f})"
            })

        if pps_z > self.threshold:
            alerts.append({
                "type": "warning",
                "msg": f"Anormal paket sayısı — {pps} pps (z={pps_z:.1f})"
            })

        return alerts

detector = AnomalyDetector()