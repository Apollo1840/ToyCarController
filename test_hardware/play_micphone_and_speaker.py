from flask import Flask, request, render_template, jsonify, Response
import time
import numpy as np
import pyaudio
import threading
from collections import deque
import io
import wave
import logging
from datetime import datetime
import ffmpeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Define parameters
FORMAT = pyaudio.paInt16  # Sampling format
CHANNELS = 1  # Mono

RECORD_CHUNK_SIZE = 8192
RECORD_RATE = 44100  # Sampling rate
RECORD_SAMPLE_WIDTH = 2

SPEAK_CHUNK_SIZE = 2024
SPEAK_RATE = 48000  # Sampling rate

recording_frame_queue = deque(maxlen=5)  # Adjust maxlen as needed
speaking_frame_queue = deque(maxlen=10)  # Adjust maxlen as needed

is_recording = threading.Event()
is_speaking = threading.Event()

recording_thread = None
speaking_thread = None


def start_speaking():
    def playback(in_data, stream):
        """in_data is webm_binary"""

        logger.info("keep speaking at %s", datetime.now())
        # Use FFmpeg to decode the binary data of the webm file to raw PCM data
        process = (ffmpeg.input('pipe:0', format='webm').output('pipe:', format='wav')
                   .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True))
        process.stdin.write(in_data)
        process.stdin.close()

        process.stdout.read(128)  # remove an artifact noise
        while is_speaking.is_set():
            data = process.stdout.read(SPEAK_CHUNK_SIZE)
            if not data:
                # logger.info("no stream at %s", datetime.now())
                break
            stream.write(data)

            # audio_data = np.frombuffer(data, dtype=np.int16)
            # audio_data = np.clip(audio_data * 2, -32768, 32767)
            # stream.write(audio_data.astype(np.int16).tobytes())

        process.stdout.close()
        process.wait()

    # Initialize PyAudio and open a stream before entering the loop
    p = pyaudio.PyAudio()
    speak_stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=SPEAK_RATE,
                          # output_device_index=6,
                          output=True)

    try:
        is_speaking.set()
        logger.info("Speaking started at %s", datetime.now())

        while is_speaking.is_set():
            if len(speaking_frame_queue) == 0:
                time.sleep(0.1)
            else:
                # logger.info(f"current queue size: {len(speaking_frame_queue)}")
                playback(speaking_frame_queue.popleft(), speak_stream)
    finally:
        # Stop and close the stream 
        speak_stream.stop_stream()
        speak_stream.close()
        p.terminate()
        logger.info("Speaking stopped at %s", datetime.now())


def start_recording():
    def callback(in_data, frame_count, time_info, status):
        # if is_recording.is_set():
        recording_frame_queue.append(in_data)
        logger.info("Keep recording at %s", datetime.now())
        return (in_data, pyaudio.paContinue)

    p = pyaudio.PyAudio()
    recording_stream = p.open(format=FORMAT,
                              channels=CHANNELS,
                              rate=RECORD_RATE,
                              input=True,
                              # input_device_index=0,
                              frames_per_buffer=RECORD_CHUNK_SIZE,
                              stream_callback=callback)
    try:
        is_recording.set()
        logger.info("Recording started at %s", datetime.now())

        recording_stream.start_stream()
        # made-dead-loop
        while is_recording.is_set():
            time.sleep(0.1)
    finally:
        # Stop and close the stream 
        recording_stream.stop_stream()
        recording_stream.close()
        p.terminate()
        logger.info("Recording stopped at %s", datetime.now())


@app.route('/')
def index():
    return render_template('index_listen_speak.html')


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    audio_data = request.files['audio_data']
    speaking_frame_queue.append(audio_data.read())
    return "sound recorded"


@app.route('/get_audio', methods=['GET'])
def get_audio():
    def generate_wav():
        with io.BytesIO() as mem_file:
            with wave.open(mem_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(RECORD_SAMPLE_WIDTH)
                wf.setframerate(RECORD_RATE)
                while recording_frame_queue:
                    wf.writeframes(recording_frame_queue.popleft())
            mem_file.seek(0)
            yield mem_file.read()

    return Response(generate_wav(), mimetype="audio/wav")


@app.route('/speak', methods=['POST'])
def speak():
    logger.info("speak button clicked at %s", datetime.now())
    global speaking_thread
    if not is_speaking.is_set():
        speaking_thread = threading.Thread(target=start_speaking)
        speaking_thread.start()
    else:
        is_speaking.clear()
        if speaking_thread is not None:
            speaking_thread.join()
    return jsonify({"status": "speak toggled"})


@app.route('/listen', methods=['POST'])
def listen():
    logger.info("listen button clicked at %s", datetime.now())
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
    return jsonify({"status": "listen toggled"})


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), port=5000)
