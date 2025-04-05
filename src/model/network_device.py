class NetworkDevice:
    def __init__(self, ip, mac):
        self.ip = ip
        self.mac = mac
        self.attacked = False
        self.is_attacker = False
        self.is_gateway = False  # New attribute

    def to_dict(self):
        return {
            "ip": self.ip,
            "mac": self.mac,
            "attacked": self.attacked,
            "is_attacker": self.is_attacker,
            "is_gateway": self.is_gateway
        }