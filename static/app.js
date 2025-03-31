console.log("app.js loaded");
const topologyCanvas = document.getElementById('topologyCanvas');
const topologyCtx = topologyCanvas.getContext('2d');
const alertDiv = document.getElementById('alert');

function startMonitoring() {
    fetch('/api/start', { method: 'POST' })
        .then(() => console.log("Monitoring started"));
}

function stopMonitoring() {
    fetch('/api/stop', { method: 'POST' })
        .then(() => console.log("Monitoring stopped"));
}

function drawTopology(devices) {
    topologyCtx.clearRect(0, 0, topologyCanvas.width, topologyCanvas.height);
    const nodeRadius = 20;
    const centerX = topologyCanvas.width / 2;
    const centerY = topologyCanvas.height / 2;
    const radius = Math.min(topologyCanvas.width, topologyCanvas.height) / 3;
    const angleStep = (2 * Math.PI) / devices.length;

    devices.forEach((device, index) => {
        const x = centerX + radius * Math.cos(angleStep * index);
        const y = centerY + radius * Math.sin(angleStep * index);

        topologyCtx.beginPath();
        topologyCtx.arc(x, y, nodeRadius, 0, Math.PI * 2);
        
        if (device.is_attacker) {
            topologyCtx.fillStyle = 'red';
            topologyCtx.fill();
        } else if (device.attacked) {
            topologyCtx.fillStyle = 'orange';
            topologyCtx.fill();
        } else {
            topologyCtx.fillStyle = 'blue';
            topologyCtx.fill();
        }
        
        topologyCtx.stroke();

        topologyCtx.fillStyle = 'black';
        topologyCtx.font = '12px Arial';
        topologyCtx.textAlign = 'center';
        const text = `${device.ip} (${device.mac})`;
        topologyCtx.fillText(text, x, y + nodeRadius + 15);
    });
}

function updateUI() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            drawTopology(devices);
            const attacked = devices.some(d => d.attacked || d.is_attacker);
            alertDiv.textContent = attacked ? "Attack Detected!" : "Network Safe";
        })
        .catch(err => console.error("Error fetching devices:", err));
}

setInterval(updateUI, 1000);
updateUI();