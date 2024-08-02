from flask import Flask, render_template, jsonify, Response
import time
import pyaudio
import threading
from collections import deque
import io
import wave
import logging
from datetime import datetime

app = Flask(__name__)

# Define parameters
CHUNK = 8192
FORMAT = pyaudio.paInt16  # Sampling format
CHANNELS = 1  # Mono
RATE = 44100  # Sampling rate
frame_queue = deque(maxlen=5)  # Adjust maxlen as needed

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

    # made-dead-loop
    while is_recording.is_set():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()
    logger.info("Recording stopped at %s", datetime.now())


def callback(in_data, frame_count, time_info, status):
    if is_recording.is_set():
        frame_queue.append(in_data)
        logger.info("Keep recording at %s", datetime.now())
    return (in_data, pyaudio.paContinue)


@app.route('/')
def index():
    return render_template('index_listen.html')


@app.route('/get_audio', methods=['GET'])
def get_audio():
    def generate_wav():
        with io.BytesIO() as mem_file:
            with wave.open(mem_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                while frame_queue:
                    wf.writeframes(frame_queue.popleft())
            mem_file.seek(0)
            yield mem_file.read()

    return Response(generate_wav(), mimetype="audio/wav")


@app.route('/listen', methods=['POST'])
def listen():
    global recording_thread
    if not is_recording.is_set():
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.start()
        time.sleep(0.1)  # wait queue to fill in with its first frame
    else:
        is_recording.clear()
        if recording_thread is not None:
            recording_thread.join()
    return jsonify({"status": "listening toggled"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
