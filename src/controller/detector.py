from scapy.all import sniff
from scapy.layers.l2 import ARP
import threading
from ..model.arp_cache import ARPCache

class ARPSpooferDetector:
    def __init__(self):
        # Create an instance of ARPCache to store and manage network device data
        self.cache = ARPCache()
        self.running = False
        self.thread = None

    # Extract the source MAC address from the ARP packet
    def process_packet(self, packet):
        # Check if the packet contains an ARP layer
        if packet.haslayer(ARP):
            # Extract the source IP address from the ARP packet
            ip = packet[ARP].psrc
            # Extract the source MAC address from the ARP packet
            mac = packet[ARP].hwsrc
            # Pass the IP and MAC to the cache for spoofing detection
            self.cache.update(ip, mac)  # Updates device state and checks for attacks

    # Method to start sniffing ARP packets
    def start_sniffing(self):
        # Only start if not already running (prevents duplicate threads)
        if not self.running:
            self.running = True
            # Enable attack detection in the cache (monitoring mode on)
            self.cache.start_monitoring()  # Tells cache to start looking for spoofing
            # Create a new thread to run the sniffing process, targeting _sniff_thread
            self.thread = threading.Thread(target=self._sniff_thread, args=("eth0",))
            self.thread.start()

    def _sniff_thread(self, iface):
        while self.running:
            # Use Scapy's sniff function to capture packets
            # iface: Network interface to listen on (e.g., "eth0")
            # filter: Only capture ARP packets
            # prn: Callback function (process_packet) to handle each packet
            # store: 0 means don’t store packets in memory (saves resources)
            # timeout: 1 second timeout to allow loop to check running flag
            sniff(iface=iface, filter="arp", prn=self.process_packet, store=0, timeout=1)

    def stop_sniffing(self):
        if self.running:
            self.running = False
            # Disable attack detection in the cache, but keep periodic scanning
            self.cache.stop_monitoring()  # Stops spoofing checks, not device updates
            if self.thread:
                self.thread.join(timeout=2)
                if self.thread.is_alive():
                    print("Warning: Sniff thread did not stop cleanly")
                self.thread = None