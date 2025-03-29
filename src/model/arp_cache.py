from .network_device import NetworkDevice
from .arp_event import ARPEvent
import scapy.all as scapy
from datetime import datetime
from collections import defaultdict

scapy.conf.iface = "eth0"
detector_mac = scapy.get_if_hwaddr("eth0")
detector_ip = "192.168.154.129"

class ARPCache:
    def __init__(self):
        self.baseline_cache = {}
        self.mac_ip_cache = {}
        self.events = []
        self.devices = {}
        self.spoof_count = defaultdict(int)
        self.build_baseline()

    def build_baseline(self):
        arp_request = scapy.ARP(pdst="192.168.154.0/24")
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=5, verbose=False)[0]
        for sent, received in answered_list:
            self.baseline_cache[received.psrc] = received.hwsrc
            self.mac_ip_cache[received.hwsrc] = received.psrc
            self.devices[received.hwsrc] = NetworkDevice(received.psrc, received.hwsrc)
        # Force Detector's own mapping
        self.baseline_cache[detector_ip] = detector_mac
        self.mac_ip_cache[detector_mac] = detector_ip
        self.devices[detector_mac] = NetworkDevice(detector_ip, detector_mac)
        print("Baseline established:", self.baseline_cache)

    def get_mac(self, ip):
        if ip == detector_ip:
            return detector_mac
        arp_request = scapy.ARP(pdst=ip)
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
        return answered_list[0][1].hwsrc if answered_list else None

    def get_ip(self, mac):
        if mac == detector_mac:
            return detector_ip
        if mac in self.mac_ip_cache:
            return self.mac_ip_cache[mac]
        arp_request = scapy.ARP(pdst="192.168.154.0/24")
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]
        for sent, received in answered_list:
            if received.hwsrc == mac:
                self.mac_ip_cache[mac] = received.psrc
                return received.psrc
        return None

    def update(self, ip, mac):
        if ip in self.baseline_cache:
            real_mac = self.baseline_cache[ip]
            if real_mac != mac:
                self.spoof_count[(ip, mac)] += 1
                if self.spoof_count[(ip, mac)] >= 3:
                    attacker_ip = self.get_ip(mac)
                    if attacker_ip and attacker_ip != ip:
                        event = ARPEvent(ip, real_mac, mac, attacker_ip, datetime.now())
                        self.events.append(event)
                        self.devices[real_mac].attacked = True
                        if mac in self.devices:
                            self.devices[mac].is_attacker = True
                        else:
                            self.devices[mac] = NetworkDevice(attacker_ip, mac)
                            self.devices[mac].is_attacker = True
                        self.spoof_count[(ip, mac)] = 0
                        return event
            else:
                self.spoof_count[(ip, mac)] = 0
        else:
            # New device
            self.baseline_cache[ip] = mac
            self.mac_ip_cache[mac] = ip
            self.devices[mac] = NetworkDevice(ip, mac)
        return None

    def get_devices(self):
        return list(self.devices.values())

    def get_events(self):
        return self.events