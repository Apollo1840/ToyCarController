from flask import Flask, render_template, jsonify, Response
import time
import pyaudio
import threading
import queue
import io
import wave

app = Flask(__name__)

# Define parameters
CHUNK = 8192
FORMAT = pyaudio.paInt16  # Sampling format
CHANNELS = 1  # Mono
RATE = 44100  # Sampling rate

frames = queue.Queue(maxsize=100)  # Limited length queue
is_recording = threading.Event()
stream = None
p = pyaudio.PyAudio()
recording_thread = None


def start_recording():
    global frames, stream
    frames.queue.clear()
    is_recording.set()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    stream.start_stream()

    while is_recording.is_set():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()


def stop_recording():
    is_recording.clear()
    if recording_thread is not None:
        recording_thread.join()


def callback(in_data, frame_count, time_info, status):
    if is_recording.is_set():
        if frames.full():
            frames.get_nowait()
        frames.put(in_data)
    return (in_data, pyaudio.paContinue)


@app.route('/')
def index():
    return render_template('index_web3.html')


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


@app.route('/get_audio', methods=['GET'])
def get_audio():
    def generate_wav():
        with io.BytesIO() as mem_file:
            with wave.open(mem_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                while not frames.empty():
                    wf.writeframes(frames.get())
            mem_file.seek(0)
            yield mem_file.read()
    return Response(generate_wav(), mimetype="audio/wav")


if __name__ == "__main__":
    app.run(debug=True)
