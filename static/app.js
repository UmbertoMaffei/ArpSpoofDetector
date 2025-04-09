console.log("app.js loaded");

// Get references to HTML elements by their IDs for manipulation
const topologyCanvas = document.getElementById('topologyCanvas');
const topologyCtx = topologyCanvas.getContext('2d');
const alertDiv = document.getElementById('alert');
const notificationDiv = document.getElementById('notification');
const monitoringStatusDiv = document.getElementById('monitoringStatus');

// Load images for visualizing different types of network devices
const normalHostImage = new Image();
normalHostImage.src = '/static/images/normal-host.svg';
const attackedHostImage = new Image();
attackedHostImage.src = '/static/images/attacked-host.svg';
const attackerHostImage = new Image();
attackerHostImage.src = '/static/images/attacker-host.svg';
const gatewayImage = new Image();
gatewayImage.src = '/static/images/gateway.svg';

// Variable to track whether monitoring is active
let isMonitoring = false; // Track monitoring state

function resizeCanvas() {
    topologyCanvas.width = topologyCanvas.offsetWidth;
    topologyCanvas.height = topologyCanvas.offsetHeight;
}
window.addEventListener('resize', () => { resizeCanvas(); updateUI(); });
resizeCanvas();

function showNotification(message) {
    notificationDiv.textContent = message;
    notificationDiv.classList.add('show');
    setTimeout(() => notificationDiv.classList.remove('show'), 2000);
}

// Function to start network monitoring by calling the backend API
function startMonitoring() {
    fetch('/api/start', { method: 'POST' })
        .then(() => {
            console.log("Monitoring started");
            isMonitoring = true;
            monitoringStatusDiv.textContent = "Monitoring: Active";
            monitoringStatusDiv.classList.add('active');
            showNotification("🛡️ Monitoring Started!");
        });
}

// Function to stop network monitoring by calling the backend API
function stopMonitoring() {
    fetch('/api/stop', { method: 'POST' })
        .then(() => {
            console.log("Monitoring stopped");
            isMonitoring = false;
            monitoringStatusDiv.textContent = "Monitoring: Stopped";
            monitoringStatusDiv.classList.remove('active');
            showNotification("🛑 Monitoring Stopped!");
            resetNetworkState();
        });
}

// Variable and interval to toggle a flashing effect for attacked/attacker devices
let flashState = true;
setInterval(() => { flashState = !flashState; updateUI(); }, 500);

// Function to draw the network topology on the canvas
function drawTopology(devices) {
    topologyCtx.clearRect(0, 0, topologyCanvas.width, topologyCanvas.height);
    const nodeSize = 50;
    const centerX = topologyCanvas.width / 2;
    const centerY = topologyCanvas.height / 2;
    const radius = Math.min(topologyCanvas.width, topologyCanvas.height) / 2.5;

    const gateway = devices.find(d => d.is_gateway) || devices[0];
    const hosts = devices.filter(d => !d.is_gateway);

    topologyCtx.globalAlpha = 0.4;
    hosts.forEach((device, index) => {
        const x = centerX + radius * Math.cos((2 * Math.PI / hosts.length) * index) - nodeSize / 2;
        const y = centerY + radius * Math.sin((2 * Math.PI / hosts.length) * index) - nodeSize / 2;

        topologyCtx.beginPath();
        topologyCtx.moveTo(centerX, centerY);
        topologyCtx.lineTo(x + nodeSize / 2, y + nodeSize / 2);
        if ((device.attacked || device.is_attacker) && flashState) {
            topologyCtx.strokeStyle = 'red';
        } else {
            topologyCtx.strokeStyle = 'white';
        }
        topologyCtx.lineWidth = 2;
        topologyCtx.stroke();
    });
    topologyCtx.globalAlpha = 1.0;

    if (gateway) {
        topologyCtx.drawImage(gatewayImage, centerX - nodeSize / 2, centerY - nodeSize / 2, nodeSize, nodeSize);
        topologyCtx.fillStyle = 'white';
        topologyCtx.font = '14px Arial';
        topologyCtx.textAlign = 'center';
        topologyCtx.fillText(`${gateway.ip} (${gateway.mac})`, centerX, centerY + nodeSize + 15);
    }

    hosts.forEach((device, index) => {
        const x = centerX + radius * Math.cos((2 * Math.PI / hosts.length) * index) - nodeSize / 2;
        const y = centerY + radius * Math.sin((2 * Math.PI / hosts.length) * index) - nodeSize / 2;

        if (device.is_attacker) {
            topologyCtx.drawImage(attackerHostImage, x, y, nodeSize, nodeSize);
        } else if (device.attacked) {
            topologyCtx.drawImage(attackedHostImage, x, y, nodeSize, nodeSize);
        } else {
            topologyCtx.drawImage(normalHostImage, x, y, nodeSize, nodeSize);
        }

        topologyCtx.fillStyle = 'white';
        topologyCtx.font = '14px Arial';
        topologyCtx.textAlign = 'center';
        const text = `${device.ip} (${device.mac})`;
        topologyCtx.fillText(text, x + nodeSize / 2, y + nodeSize + 15);
    });
}

// Function to reset the network state and update the UI (Network Safe)
function resetNetworkState() {
    fetch('/api/devices', { cache: 'no-store' })
        .then(response => response.json())
        .then(devices => {
            devices.forEach(device => {
                device.attacked = false;
                device.is_attacker = false;
            });
            console.log("Reset network state with devices:", devices);
            drawTopology(devices);
            alertDiv.textContent = "Network Safe";
            alertDiv.classList.remove('alert-active');
        })
        .catch(err => console.error("Error resetting network state:", err));
}

// Function to periodically update the UI with the latest device data
function updateUI() {
    fetch('/api/devices', { cache: 'no-store' })
        .then(response => response.json())
        .then(devices => {
            console.log("Updating UI with devices:", devices);
            drawTopology(devices);
            const attacked = devices.some(d => d.attacked || d.is_attacker);
            alertDiv.textContent = attacked ? "Attack Detected!" : "Network Safe";
            alertDiv.classList.toggle('alert-active', attacked);
        })
        .catch(err => console.error("Error fetching devices:", err));
}

// Set an interval to update the UI every 1 second
setInterval(updateUI, 1000);

// Call updateUI immediately to initialize the display
updateUI();