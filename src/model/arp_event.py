class ARPEvent:
    def __init__(self, ip, old_mac, new_mac, attacker_ip, timestamp):
        self.ip = ip
        self.old_mac = old_mac
        self.new_mac = new_mac
        self.attacker_ip = attacker_ip
        self.timestamp = timestamp

    def to_dict(self):
        return {
            'ip': self.ip,
            'old_mac': self.old_mac,
            'new_mac': self.new_mac,
            'attacker_ip': self.attacker_ip,
            'timestamp': self.timestamp.isoformat()
        }