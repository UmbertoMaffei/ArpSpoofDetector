from scapy.all import sniff
from scapy.layers.l2 import ARP
import threading
from ..model.arp_cache import ARPCache

class ARPSpooferDetector:
    def __init__(self):
        self.cache = ARPCache()
        self.running = False
        self.thread = None

    def process_packet(self, packet):
        if packet.haslayer(ARP):
            ip = packet[ARP].psrc
            mac = packet[ARP].hwsrc
            self.cache.update(ip, mac)

    def start_sniffing(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._sniff_thread, args=("eth0",))
            self.thread.start()

    def _sniff_thread(self, iface):
        while self.running:
            sniff(iface=iface, filter="arp", prn=self.process_packet, store=0, timeout=1)

    def stop_sniffing(self):
        if self.running:
            self.running = False
            self.cache.stop_scan()  # Stop periodic scan
            if self.thread:
                self.thread.join(timeout=2)
                if self.thread.is_alive():
                    print("Warning: Sniff thread did not stop cleanly")
                self.thread = None