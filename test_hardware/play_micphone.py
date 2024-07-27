from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pyaudio
import numpy as np
import threading
import scipy.signal

app = Flask(__name__)
socketio = SocketIO(app)

# Audio parameters
CHUNK = 4096  # Increased chunk size for smoother streaming
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Global variables to manage the audio stream and thread
stream = None
streaming_thread = None
streaming = False

p = pyaudio.PyAudio()


def audio_stream():
    global stream, streaming
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    b, a = scipy.signal.butter(6, 0.1, btype='low')  # Low-pass filter parameters
    volume_history = []

    while streaming:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Apply low-pass filter
        filtered_data = scipy.signal.lfilter(b, a, audio_data)

        # Compute volume
        volume = np.linalg.norm(filtered_data) / (CHUNK * 48)
        volume_history.append(volume)
        if len(volume_history) > 5:
            volume_history.pop(0)

        smoothed_volume = np.mean(volume_history)
        if smoothed_volume > 1:
            smoothed_volume = 1

        socketio.emit('volume', {'volume': smoothed_volume, 'audio_data': filtered_data.tobytes().hex()})

    stream.stop_stream()
    stream.close()


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('start_listening')
def start_listening():
    global streaming, streaming_thread
    if not streaming:
        streaming = True
        streaming_thread = threading.Thread(target=audio_stream)
        streaming_thread.start()
        emit('listening_status', {'status': 'started'})


@socketio.on('stop_listening')
def stop_listening():
    global streaming
    streaming = False
    emit('listening_status', {'status': 'stopped'})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
