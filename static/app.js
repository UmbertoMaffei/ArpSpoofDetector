console.log("app.js loaded");
const topologyCanvas = document.getElementById('topologyCanvas');
const topologyCtx = topologyCanvas.getContext('2d');
const alertDiv = document.getElementById('alert');
const notificationDiv = document.getElementById('notification');

const normalHostImage = new Image();
normalHostImage.src = '/static/images/normal-host.svg';
const attackedHostImage = new Image();
attackedHostImage.src = '/static/images/attacked-host.svg';
const attackerHostImage = new Image();
attackerHostImage.src = '/static/images/attacker-host.svg';

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

function startMonitoring() {
    fetch('/api/start', { method: 'POST' })
        .then(() => {
            console.log("Monitoring started");
            showNotification("🛡️ Monitoring Started!");
        });
}

function stopMonitoring() {
    fetch('/api/stop', { method: 'POST' })
        .then(() => {
            console.log("Monitoring stopped");
            showNotification("🛑 Monitoring Stopped!");
            resetNetworkState();
        });
}

function drawTopology(devices) {
    topologyCtx.clearRect(0, 0, topologyCanvas.width, topologyCanvas.height);
    const nodeSize = 50; // Fixed size, no zoom
    const centerX = topologyCanvas.width / 2;
    const centerY = topologyCanvas.height / 2;
    const radius = Math.min(topologyCanvas.width, topologyCanvas.height) / 2.5;
    const angleStep = devices.length > 1 ? (2 * Math.PI) / devices.length : 0;

    devices.forEach((device, index) => {
        const x = centerX + radius * Math.cos(angleStep * index) - nodeSize / 2;
        const y = centerY + radius * Math.sin(angleStep * index) - nodeSize / 2;

        if (device.is_attacker) {
            topologyCtx.drawImage(attackerHostImage, x, y, nodeSize, nodeSize);
        } else if (device.attacked) {
            topologyCtx.drawImage(attackedHostImage, x, y, nodeSize, nodeSize);
        } else {
            topologyCtx.drawImage(normalHostImage, x, y, nodeSize, nodeSize);
        }

        topologyCtx.fillStyle = 'white';
        topologyCtx.font = '14px Arial'; // Fixed font size
        topologyCtx.textAlign = 'center';
        const text = `${device.ip} (${device.mac})`;
        topologyCtx.fillText(text, x + nodeSize / 2, y + nodeSize + 15);
    });
}

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

setInterval(updateUI, 1000);
updateUI();