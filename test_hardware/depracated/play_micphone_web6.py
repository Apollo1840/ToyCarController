from flask import Flask, render_template, jsonify
import pyaudio
import threading
import time
import logging
from datetime import datetime
from flask_socketio import SocketIO, emit
import base64

app = Flask(__name__)
socketio = SocketIO(app)

# Define parameters
CHUNK = 8192
FORMAT = pyaudio.paInt16  # Sampling format
CHANNELS = 1  # Mono
RATE = 44100  # Sampling rate

frame = None
is_recording = threading.Event()
stream = None
p = pyaudio.PyAudio()
recording_thread = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_recording():
    global stream
    is_recording.set()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    stream.start_stream()
    logger.info("Recording started at %s", datetime.now())

    while is_recording.is_set():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()
    logger.info("Recording stopped at %s", datetime.now())

def stop_recording():
    is_recording.clear()
    if recording_thread is not None:
        recording_thread.join()

def callback(in_data, frame_count, time_info, status):
    if is_recording.is_set():
        b64_data = base64.b64encode(in_data).decode('utf-8')
        socketio.emit('audio_frame', b64_data)
        logger.info("Keep recording at %s", datetime.now())
    return (in_data, pyaudio.paContinue)

@app.route('/')
def index():
    return render_template('index_listen_dev.html')

@app.route('/start_recording', methods=['POST'])
def start():
    global recording_thread
    recording_thread = threading.Thread(target=start_recording)
    recording_thread.start()
    return jsonify({"status": "recording started"})

@app.route('/stop_recording', methods=['POST'])
def stop():
    stop_recording()
    return jsonify({"status": "recording stopped"})

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
