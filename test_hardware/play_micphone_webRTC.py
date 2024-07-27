from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import pyaudio
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Audio parameters
CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
DEVICE_INDEX = 6

# Global variables to manage the audio stream and thread
stream = None
streaming_thread = None
streaming = False


def audio_stream():
    global stream, streaming
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=DEVICE_INDEX,
                    frames_per_buffer=CHUNK)

    while streaming:
        data = stream.read(CHUNK, exception_on_overflow=False)
        socketio.emit('audio_data', {'audio_data': data.hex()})

    stream.stop_stream()
    stream.close()
    p.terminate()


@app.route('/')
def index():
    return render_template('index_rtc.html')


@socketio.on('start_listening')
def start_listening():
    global streaming, streaming_thread
    if not streaming:
        streaming = True
        streaming_thread = threading.Thread(target=audio_stream)
        streaming_thread.start()
        emit('listening_status', {'status': 'started'})
        print("Started listening")


@socketio.on('stop_listening')
def stop_listening():
    global streaming
    streaming = False
    emit('listening_status', {'status': 'stopped'})
    print("Stopped listening")


@socketio.on('offer')
def handle_offer(data):
    print(f"Offer received: {data}")
    emit('offer', data, broadcast=True)


@socketio.on('answer')
def handle_answer(data):
    print(f"Answer received: {data}")
    emit('answer', data, broadcast=True)


@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    print(f"ICE Candidate received: {data}")
    emit('ice-candidate', data, broadcast=True)


if __name__ == '__main__':
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
    socketio.run(app, host='0.0.0.0', port=5000)
