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
    const spacing = 150;
    let x = 50;

    devices.forEach((device, index) => {
        const y = topologyCanvas.height / 2;
        topologyCtx.beginPath();
        topologyCtx.arc(x + index * spacing, y, nodeRadius, 0, Math.PI * 2);

        if (device.is_attacker) {
            topologyCtx.fillStyle = 'red';  // Attacker
            topologyCtx.fill();  // Flash effect could be added with setInterval
        } else if (device.attacked) {
            topologyCtx.fillStyle = 'orange';  // Attacked
            topologyCtx.fill();
        } else {
            topologyCtx.fillStyle = 'blue';  // Normal
            topologyCtx.fill();
        }

        topologyCtx.stroke();
        topologyCtx.fillStyle = 'black';
        topologyCtx.font = '12px Arial';
        topologyCtx.fillText(`${device.ip} (${device.mac})`, x + index * spacing - 40, y + nodeRadius + 20);
    });
}

function updateUI() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            drawTopology(devices);
            const attacked = devices.filter(d => d.attacked || d.is_attacker).length > 0;
            alertDiv.textContent = attacked ? "Attack Detected!" : "";
        })
        .catch(err => console.error("Error fetching devices:", err));
}

// Poll every 2 seconds
setInterval(updateUI, 2000);
updateUI();  // Initial draw