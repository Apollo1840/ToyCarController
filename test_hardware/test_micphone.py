from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pyaudio
import numpy as np
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Audio parameters
CHUNK = 2048  # Increased buffer size
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Global variables to manage the audio stream and thread
p = pyaudio.PyAudio()
stream = None
streaming_thread = None
streaming = False


def audio_stream():
    global stream, streaming
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=DEVICE_INDEX,
                    frames_per_buffer=CHUNK)

    while streaming:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        # Normalize volume between 0 and 1
        volume = np.linalg.norm(audio_data) / (CHUNK * 32767)
        if volume > 1:
            volume = 1
        socketio.emit('volume', {'volume': volume})

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
    # List audio devices and ask the user to select one
    def list_audio_devices():
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                print(f"Device ID {i} - {device_info.get('name')}")
        p.terminate()


    list_audio_devices()
    DEVICE_INDEX = int(input("Enter the device index to use for recording: "))

    # Start the Flask server
    socketio.run(app, host='0.0.0.0', port=5000)
