from flask import Flask, jsonify, send_from_directory
from .controller.detector import ARPSpooferDetector
import os

app = Flask(__name__, static_folder="../static")
detector = ARPSpooferDetector()

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = [d.to_dict() for d in detector.cache.get_devices()]
    return jsonify(devices)

@app.route('/api/events', methods=['GET'])
def get_events():
    events = [e.to_dict() for e in detector.cache.get_events()]
    return jsonify(events)

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    detector.start_sniffing()
    return jsonify({'status': 'started'})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    detector.stop_sniffing()
    return jsonify({'status': 'stopped'})

if __name__ == "__main__":
    if not os.path.exists('../static'):
        os.makedirs('../static')
    app.run(host='0.0.0.0', port=5000, debug=True)