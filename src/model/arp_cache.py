from .network_device import NetworkDevice
from .arp_event import ARPEvent
import scapy.all as scapy
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time
import subprocess

scapy.conf.iface = "eth0"
detector_mac = scapy.get_if_hwaddr("eth0")
detector_ip = scapy.get_if_addr("eth0")

class ARPCache:
    def __init__(self):
        # Dictionary to store baseline IP-to-MAC mappings (trusted state)
        self.baseline_cache = {}
        # Dictionary to store reverse MAC-to-IP mappings for quick lookups
        self.mac_ip_cache = {}
        # List to store ARP spoofing events
        self.events = []
        # Dictionary to store current devices (IP -> NetworkDevice objects)
        self.devices = {}
        # Defaultdict to count spoof attempts per (IP, MAC) pair
        self.spoof_count = defaultdict(int)
        # Track the last time a spoof was detected for timeout logic
        self.last_spoof_time = datetime.now()
        # Detect and store the gateway (router) IP address
        self.gateway_ip = self.get_gateway_ip()
        # Build the initial network baseline
        self.build_baseline()
        # Reset attack-related states (e.g., attacked, is_attacker flags)
        self.reset_states()
        # Flag to control the periodic scanning thread
        self.scan_running = True
        # Flag to enable/disable spoofing detection (monitoring mode)
        self.monitoring_active = False
        # Flag to enable/disable spoofing detection (monitoring mode)
        self.scan_thread = threading.Thread(target=self._periodic_scan, daemon=True)
        # Start the scanning thread immediately
        self.scan_thread.start()

    # Method to detect the default gateway IP using system routing table
    def get_gateway_ip(self):
        # Use system command to get default gateway
        try:
            result = subprocess.check_output(["ip", "route"]).decode("utf-8")
            for line in result.splitlines():
                if "default via" in line:
                    return line.split()[2]  # e.g., "192.168.154.2"
        except Exception as e:
            print(f"Error detecting gateway: {e}")
            return "192.168.154.2"  # Fallback (adjust if needed)
        return None

    # Method to build the initial trusted baseline of IP-to-MAC mappings
    def build_baseline(self):
        # Create an ARP request for the entire subnet (192.168.154.0/24)
        arp_request = scapy.ARP(pdst="192.168.154.0/24")
        # Create a broadcast Ethernet frame to send the ARP request
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        # Combine ARP request with broadcast frame
        arp_request_broadcast = broadcast / arp_request
        # Send the request and receive responses (timeout after 5 seconds)
        answered_list = scapy.srp(arp_request_broadcast, timeout=5, verbose=False)[0]
        # Process each response
        for sent, received in answered_list:
            # Store IP-to-MAC mapping in baseline cache
            self.baseline_cache[received.psrc] = received.hwsrc
            # Store reverse MAC-to-IP mapping
            self.mac_ip_cache[received.hwsrc] = received.psrc
            # Create a NetworkDevice object and store it in devices dict
            self.devices[received.psrc] = NetworkDevice(received.psrc, received.hwsrc)
            # Mark the device as the gateway if its IP matches gateway_ip
            if received.psrc == self.gateway_ip:
                self.devices[received.psrc].is_gateway = True
        # Manually add the Detector VM to the caches
        self.baseline_cache[detector_ip] = detector_mac
        self.mac_ip_cache[detector_mac] = detector_ip
        self.devices[detector_ip] = NetworkDevice(detector_ip, detector_mac)
        # Check if Detector VM is the gateway
        if detector_ip == self.gateway_ip:
            self.devices[detector_ip].is_gateway = True
        # Log the established baseline for debugging
        print("Baseline established:", {ip: dev.to_dict() for ip, dev in self.devices.items()})

    # Private method to periodically scan the network for live devices
    def _periodic_scan(self):
        # Run while the scan thread is active
        while self.scan_running:
            # Temporary dict to store live devices from this scan
            live_devices = {}
            # Send ARP request to the entire subnet
            arp_request = scapy.ARP(pdst="192.168.154.0/24")
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request
            answered_list = scapy.srp(arp_request_broadcast, timeout=5, verbose=False)[0]
            # Populate live_devices with responses
            for sent, received in answered_list:
                live_devices[received.psrc] = received.hwsrc
            # Ensure Detector VM is always considered live
            live_devices[detector_ip] = detector_mac

            # Copy current devices to update them
            current_devices = self.devices.copy()
            # Update or add devices based on live scan
            for ip, mac in live_devices.items():
                if ip in current_devices:
                    # Update MAC if it changed (rare but possible)
                    current_devices[ip].mac = mac
                else:
                    # Add new device if not previously known
                    current_devices[ip] = NetworkDevice(ip, mac)
                    if ip == self.gateway_ip:
                        current_devices[ip].is_gateway = True
                print(f"New device detected: {ip} -> {mac}")
            # Update self.devices to only include live devices
            self.devices = {ip: dev for ip, dev in current_devices.items() if ip in live_devices}
            # Log the updated live devices
            print("Live devices updated:", {ip: dev.to_dict() for ip, dev in self.devices.items()})
            time.sleep(30)

    # Method to get the MAC address for a given IP
    def get_mac(self, ip):
        # Return Detector VM's MAC if IP matches
        if ip == detector_ip:
            return detector_mac
        # Send targeted ARP request to the IP
        arp_request = scapy.ARP(pdst=ip)
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
        # Return MAC if response received, else None
        return answered_list[0][1].hwsrc if answered_list else None

    # Method to get the IP address for a given MAC
    def get_ip(self, mac):
        # Return Detector VM's IP if MAC matches
        if mac == detector_mac:
            return detector_ip
        # Check cache first for quick lookup
        if mac in self.mac_ip_cache:
            return self.mac_ip_cache[mac]
        # Send ARP request to the subnet to find the IP
        arp_request = scapy.ARP(pdst="192.168.154.0/24")
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]
        # Update cache and return IP if found
        for sent, received in answered_list:
            if received.hwsrc == mac:
                self.mac_ip_cache[mac] = received.psrc
                return received.psrc
        # Return None if no IP found
        return None

    # Method to update device state and detect spoofing
    def update(self, ip, mac):
        # Skip if not in monitoring mode (attack detection off)
        if not self.monitoring_active:
            return None
        # Get current timestamp
        now = datetime.now()
        # Check if IP is in the baseline
        if ip in self.baseline_cache:
            # Get the trusted MAC from baseline
            real_mac = self.baseline_cache[ip]
            # If MAC doesn’t match, potential spoofing detected
            if real_mac != mac:
                # Increment spoof attempt counter for this (IP, MAC) pair
                self.spoof_count[(ip, mac)] += 1
                self.last_spoof_time = now
                print(f"Spoof detected for {ip}: {real_mac} -> {mac}, count: {self.spoof_count[(ip, mac)]}")
                # If 3+ spoof attempts, confirm attack
                if self.spoof_count[(ip, mac)] >= 3:
                    # Find the attacker’s IP from the spoofed MAC
                    attacker_ip = self.get_ip(mac)
                    if attacker_ip and attacker_ip != ip:
                        # Create an ARP event to log the attack
                        event = ARPEvent(ip, real_mac, mac, attacker_ip, now)
                        self.events.append(event)
                        # Mark the victim as attacked
                        self.devices[ip].attacked = True
                        # Mark the attacker if already known
                        if attacker_ip in self.devices:
                            self.devices[attacker_ip].is_attacker = True
                        else:
                            # Add attacker as a new device
                            self.devices[attacker_ip] = NetworkDevice(attacker_ip, mac)
                            self.devices[attacker_ip].is_attacker = True
                        # Reset spoof counter after confirmed attack
                        self.spoof_count[(ip, mac)] = 0
                        print(f"Event added: {event.to_dict()}")
                        return event
            else:
                # Reset spoof counter if MAC matches baseline
                self.spoof_count[(ip, mac)] = 0
                # Reset states if no spoofs for 5.2 seconds
                if now - self.last_spoof_time > timedelta(seconds=5.2):
                    self.reset_states()
                    print("States reset due to timeout")
        else:
            # New device: add to baseline and caches
            self.baseline_cache[ip] = mac
            self.mac_ip_cache[mac] = ip
            if ip not in self.devices:
                self.devices[ip] = NetworkDevice(ip, mac)
                if ip == self.gateway_ip:
                    self.devices[ip].is_gateway = True
            print(f"New device added: {ip} -> {mac}")
        return None

    # Method to return the list of current devices
    def get_devices(self):
        # Method to return the list of ARP events
        devices_list = list(self.devices.values())
        print("Returning devices from get_devices:", [d.to_dict() for d in devices_list])
        return devices_list

    # Method to return the list of ARP events
    def get_events(self):
        return self.events

    # Convert devices dict to a list of NetworkDevice objects
    def reset_states(self):
        # Method to reset attack-related states
        for dev in self.devices.values():
            dev.attacked = False
            dev.is_attacker = False
        self.events.clear()
        self.spoof_count.clear()
        print("All device states reset")

    # Method to enable attack detection
    def start_monitoring(self):
        self.monitoring_active = True
        print("Monitoring activated")

    # Method to disable attack detection but keep scanning
    def stop_monitoring(self):
        self.monitoring_active = False
        self.reset_states()
        print("Monitoring deactivated, scanning continues")

    # Method to fully stop the periodic scan
    def stop_scan(self):
        self.scan_running = False
        self.reset_states()
        print("Scanning stopped")