from flask import Flask, render_template, request, jsonify
import pyaudio
import threading
from collections import deque
import logging
from datetime import datetime
import wave
import io
import subprocess
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

# Define parameters
CHUNK = 8192
FORMAT = pyaudio.paInt16  # Sampling format
CHANNELS = 1  # Mono
RATE = 44100  # Sampling rate
frame_queue = deque()  # Queue to hold the audio frames

is_speaking = threading.Event()
stream = None
p = pyaudio.PyAudio()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_to_wav(audio_data):
    print(audio_data[:10])  # Print the first 10 bytes to inspect the format

    process = subprocess.Popen(
        [ffmpeg.get_ffmpeg_exe(), '-i', 'pipe:0', '-f', 'wav', 'pipe:1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    wav_data, stderr = process.communicate(input=audio_data)

    # Log stderr to check for errors during conversion
    if process.returncode != 0:
        print("FFmpeg error:", stderr.decode())
        return None

    return wav_data


def play_audio():
    global stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)

    while is_speaking.is_set():
        if frame_queue:
            data = frame_queue.popleft()
            stream.write(data)

    stream.stop_stream()
    stream.close()


@app.route('/')
def index():
    return render_template('index_speak_basic.html')


@app.route('/start_speaking', methods=['POST'])
def start_speaking():
    is_speaking.set()
    threading.Thread(target=play_audio).start()
    logger.info("Speaking started at %s", datetime.now())
    return jsonify({"status": "speaking started"})


@app.route('/end_speaking', methods=['POST'])
def end_speaking():
    is_speaking.clear()
    logger.info("Speaking stopped at %s", datetime.now())
    return jsonify({"status": "speaking stopped"})


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    print(f"Uploading audio... {is_speaking.is_set()}")
    if is_speaking.is_set():
        audio_data = request.files['audio_data'].read()

        wav_data = convert_to_wav(audio_data)
        if wav_data is None:
            return jsonify({"status": "conversion failed"}), 400

        try:
            # Use io.BytesIO to treat the audio_data as a file-like object
            with io.BytesIO(wav_data) as audio_io:
                with wave.open(audio_io, 'rb') as wf:
                    while True:
                        data = wf.readframes(CHUNK)
                        if not data:
                            print("data is invalid")
                            break
                        frame_queue.append(data)
                        print(f"len_queue: {len(frame_queue)} frames")

            logger.info("Audio data received and added to queue at %s", datetime.now())

        except wave.Error as e:
            return jsonify({"status": "invalid wav file", "error": str(e)}), 400

    return jsonify({"status": "audio received"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
