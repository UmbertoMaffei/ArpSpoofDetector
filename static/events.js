console.log("events.js loaded");

// Get references to HTML elements by their IDs for manipulation
const eventsBody = document.getElementById('eventsBody');
const downloadCsvBtn = document.getElementById('downloadCsvBtn');

// Function to fetch and display ARP events from the backend
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

// Function to fetch events and download them as a CSV file
function downloadCSV() {
    fetch('/api/events')
        .then(response => response.json())
        .then(events => {
            const headers = ['Victim IP', 'Old MAC', 'New MAC', 'Attacker IP', 'Timestamp'];
            const csvRows = [headers.join(',')];
            events.forEach(event => {
                const row = [
                    event.ip,
                    event.old_mac,
                    event.new_mac,
                    event.attacker_ip,
                    event.timestamp
                ].map(value => `"${value}"`).join(','); // Quote values for CSV safety
                csvRows.push(row);
            });
            const csvContent = csvRows.join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `arp_events_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(err => console.error("Error downloading CSV:", err));
}

downloadCsvBtn.addEventListener('click', downloadCSV);

// Set an interval to update the events table every 1 second
setInterval(updateEvents, 1000);
updateEvents();