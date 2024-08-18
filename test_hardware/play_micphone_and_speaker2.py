import io
import threading
from collections import deque
import logging
import time
from datetime import datetime
import numpy as np
from flask import Flask, request, render_template, jsonify, Response
import pyaudio
import wave
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
speaking_frame_queue = deque(maxlen=50)  # Adjust maxlen as needed
speaking_audio_queue = deque(maxlen=1000)

is_recording = threading.Event()
is_speaking = threading.Event()

recording_thread = None
speaking_thread = None


def webm_to_pyaudio():
    global speaking_frame_queue, speaking_audio_queue

    while True:
        if len(speaking_frame_queue) == 0:
            time.sleep(0.1)
            continue

        # Start a single FFmpeg process
        process = (ffmpeg.input('pipe:0', format='webm').output('pipe:', format='wav')
                   .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True))

        while len(speaking_frame_queue) > 0:
            in_data = speaking_frame_queue.popleft()
            process.stdin.write(in_data)

        process.stdin.close()

        process.stdout.read(128)  # Remove an artifact noise

        while True:
            data = process.stdout.read(SPEAK_CHUNK_SIZE)
            if not data:
                break
            speaking_audio_queue.append(data)

        process.stdout.close()
        process.wait()

        logger.info(f"webm_to_pyaudio thread working: length of speaking_audio_queue({len(speaking_audio_queue)})")


def start_speaking():
    def playback(stream):
        logger.info("keep speaking at %s", datetime.now())

        while is_speaking.is_set():
            if len(speaking_audio_queue) == 0:
                time.sleep(0.1)
                continue

            data = speaking_audio_queue.popleft()
            stream.write(data)

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
            if len(speaking_audio_queue) == 0:
                time.sleep(0.1)
            else:
                # logger.info(f"current queue size: {len(speaking_frame_queue)}")
                playback(speak_stream)
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
    global speaking_thread, speaking_thread_data_process
    if not is_speaking.is_set():
        speaking_thread_data_process = threading.Thread(target=webm_to_pyaudio)
        speaking_thread_data_process.start()
        speaking_thread = threading.Thread(target=start_speaking)
        speaking_thread.start()

    else:
        is_speaking.clear()
        if speaking_thread is not None:
            speaking_thread.join()
            speaking_thread_data_process.join()
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
