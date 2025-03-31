console.log("events.js loaded");
const eventsBody = document.getElementById('eventsBody');

function updateEvents() {
    fetch('/api/events')
        .then(response => response.json())
        .then(events => {
            eventsBody.innerHTML = ''; // Clear existing rows
            events.forEach(event => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${event.ip}</td>
                    <td>${event.old_mac}</td>
                    <td>${event.new_mac}</td>
                    <td>${event.attacker_ip}</td>
                    <td>${event.timestamp}</td>
                `;
                eventsBody.appendChild(row);
            });
        })
        .catch(err => console.error("Error fetching events:", err));
}

setInterval(updateEvents, 1000); // Update every 1 second
updateEvents(); // Initial call