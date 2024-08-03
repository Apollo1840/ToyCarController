from flask import Flask, render_template, request, jsonify
import time
from collections import deque
import pyaudio
import ffmpeg
import threading
import logging
from datetime import datetime

app = Flask(__name__)

# Define parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16  # Sampling format
CHANNELS = 1  # Mono
RATE = 48000  # Sampling rate
frame_queue = deque(maxlen=20)  # Adjust maxlen as needed

is_recording = threading.Event()
stream = None
p = pyaudio.PyAudio()
recording_thread = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_recording():
    # record from client and speak
    is_recording.set()
    logger.info("Recording started at %s", datetime.now())
    time.sleep(2)
    while is_recording.is_set():
        if len(frame_queue) == 0:
            time.sleep(0.1)
        else:
            logger.info("speaking at %s", datetime.now())
            logger.info(f"current queue size: {len(frame_queue)}")
            speak(frame_queue.popleft())

    logger.info("Recording stopped at %s", datetime.now())


def speak(wav_binary):
    # Use FFmpeg to decode the binary data of the webm file to raw PCM data
    process = (
        ffmpeg
            .input('pipe:0', format='webm')
            .output('pipe:', format='wav')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    # Feed the binary data to ffmpeg's stdin
    process.stdin.write(wav_binary)
    process.stdin.close()

    # Read the first few bytes of the WAV header to determine the sample rate and number of channels
    # wav_header = process.stdout.read(44)  # WAV header is 44 bytes
    # channels = int.from_bytes(wav_header[22:24], byteorder='little')
    # sample_rate = int.from_bytes(wav_header[24:28], byteorder='little')

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream with PyAudio for playback
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    # output_device_index=6,
                    output=True)

    while is_recording.is_set():
        data = process.stdout.read(CHUNK)
        if not data:
            break
        logger.info("streaming at %s", datetime.now())
        stream.write(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    process.stdout.close()
    process.wait()
    logger.info("speak ends at %s", datetime.now())


@app.route('/')
def index():
    return render_template('index_speak_pc.html')


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    frame_queue.append(request.files['audio_data'].read())
    return "sound recorded"


@app.route('/speak', methods=['POST'])
def listen():
    global recording_thread
    if not is_recording.is_set():
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.start()
    else:
        is_recording.clear()
        if recording_thread is not None:
            recording_thread.join()
    return jsonify({"status": "speak toggled"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
