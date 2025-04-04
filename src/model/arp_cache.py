from .network_device import NetworkDevice
from .arp_event import ARPEvent
import scapy.all as scapy
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time

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
        self.last_spoof_time = datetime.now()
        self.build_baseline()
        self.reset_states()
        self.scan_thread = threading.Thread(target=self._periodic_scan, daemon=True)
        self.scan_running = True
        self.scan_thread.start()

    def build_baseline(self):
        arp_request = scapy.ARP(pdst="192.168.154.0/24")
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=5, verbose=False)[0]
        for sent, received in answered_list:
            self.baseline_cache[received.psrc] = received.hwsrc
            self.mac_ip_cache[received.hwsrc] = received.psrc
            self.devices[received.psrc] = NetworkDevice(received.psrc, received.hwsrc)
        self.baseline_cache[detector_ip] = detector_mac
        self.mac_ip_cache[detector_mac] = detector_ip
        self.devices[detector_ip] = NetworkDevice(detector_ip, detector_mac)
        print("Baseline established:", {ip: dev.to_dict() for ip, dev in self.devices.items()})

    def _periodic_scan(self):
        while self.scan_running:
            live_devices = {}
            arp_request = scapy.ARP(pdst="192.168.154.0/24")
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request
            answered_list = scapy.srp(arp_request_broadcast, timeout=5, verbose=False)[0]
            for sent, received in answered_list:
                live_devices[received.psrc] = received.hwsrc
            live_devices[detector_ip] = detector_mac

            current_devices = self.devices.copy()
            for ip, mac in live_devices.items():
                if ip in current_devices:
                    current_devices[ip].mac = mac
                else:
                    current_devices[ip] = NetworkDevice(ip, mac)
                    print(f"New device detected: {ip} -> {mac}")
            self.devices = {ip: dev for ip, dev in current_devices.items() if ip in live_devices}
            print("Live devices updated:", {ip: dev.to_dict() for ip, dev in self.devices.items()})
            time.sleep(30)

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
        now = datetime.now()
        if ip in self.baseline_cache:
            real_mac = self.baseline_cache[ip]
            if real_mac != mac:
                self.spoof_count[(ip, mac)] += 1
                self.last_spoof_time = now
                print(f"Spoof detected for {ip}: {real_mac} -> {mac}, count: {self.spoof_count[(ip, mac)]}")
                if self.spoof_count[(ip, mac)] >= 3:
                    attacker_ip = self.get_ip(mac)
                    if attacker_ip and attacker_ip != ip:
                        event = ARPEvent(ip, real_mac, mac, attacker_ip, now)
                        self.events.append(event)
                        self.devices[ip].attacked = True
                        if attacker_ip in self.devices:
                            self.devices[attacker_ip].is_attacker = True
                        else:
                            self.devices[attacker_ip] = NetworkDevice(attacker_ip, mac)
                            self.devices[attacker_ip].is_attacker = True
                        self.spoof_count[(ip, mac)] = 0
                        print(f"Event added: {event.to_dict()}")
                        return event
            else:
                self.spoof_count[(ip, mac)] = 0
                if now - self.last_spoof_time > timedelta(seconds=5.2):
                    self.reset_states()
                    print("States reset due to timeout")
        else:
            self.baseline_cache[ip] = mac
            self.mac_ip_cache[mac] = ip
            if ip not in self.devices:
                self.devices[ip] = NetworkDevice(ip, mac)
            print(f"New device added: {ip} -> {mac}")
        return None

    def get_devices(self):
        devices_list = list(self.devices.values())
        print("Returning devices from get_devices:", [d.to_dict() for d in devices_list])
        return devices_list

    def get_events(self):
        return self.events

    def reset_states(self):
        for dev in self.devices.values():
            dev.attacked = False
            dev.is_attacker = False
        self.events.clear()  # Clear events too
        self.spoof_count.clear()  # Reset spoof counts
        print("All device states reset")

    def stop_scan(self):
        self.scan_running = False
        self.reset_states()  # Reset on stop