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
FORMAT = pyaudio.paInt16  # Sampling format

RECORD_CHUNK_SIZE = 8192
RECORD_SAMPLE_WIDTH = 2
RECORD_CHANNELS = 1  # Mono
RECORD_RATE = 44100  # Sampling rate

recording_frame_queue = deque(maxlen=5)  # Adjust maxlen as needed

is_recording = threading.Event()

recording_thread = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_recording():
    def callback(in_data, frame_count, time_info, status):
        # if is_recording.is_set():
        recording_frame_queue.append(in_data)
        logger.info("Keep recording at %s", datetime.now())
        return (in_data, pyaudio.paContinue)

    p = pyaudio.PyAudio()
    is_recording.set()

    recording_stream = p.open(format=FORMAT,
                              channels=RECORD_CHANNELS,
                              rate=RECORD_RATE,
                              input=True,
                              # input_device_index=0,
                              frames_per_buffer=RECORD_CHUNK_SIZE,
                              stream_callback=callback)

    recording_stream.start_stream()
    logger.info("Recording started at %s", datetime.now())

    # made-dead-loop
    while is_recording.is_set():
        time.sleep(0.1)

    recording_stream.stop_stream()
    recording_stream.close()
    logger.info("Recording stopped at %s", datetime.now())


@app.route('/')
def index():
    return render_template('index_listen_speak.html')


@app.route('/get_audio', methods=['GET'])
def get_audio():
    def generate_wav():
        with io.BytesIO() as mem_file:
            with wave.open(mem_file, 'wb') as wf:
                wf.setnchannels(RECORD_CHANNELS)
                wf.setsampwidth(RECORD_SAMPLE_WIDTH)
                wf.setframerate(RECORD_RATE)
                while recording_frame_queue:
                    wf.writeframes(recording_frame_queue.popleft())
            mem_file.seek(0)
            yield mem_file.read()

    return Response(generate_wav(), mimetype="audio/wav")


@app.route('/listen', methods=['POST'])
def listen():
    global recording_thread
    if not is_recording.is_set():
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.start()

        # wait queue to fill in with its first frame, because fetch audio is after the return of this API
        time.sleep(0.5)
    else:
        is_recording.clear()
        if recording_thread is not None:
            recording_thread.join()
    return jsonify({"status": "listening toggled"})


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), port=5000)

