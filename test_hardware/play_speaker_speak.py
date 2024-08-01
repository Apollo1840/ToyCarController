from flask import Flask, render_template, request, send_file
import os
from collections import deque
import pyaudio
import ffmpeg

app = Flask(__name__)
wav_binary = deque(maxlen=3)


@app.route('/')
def index():
    return render_template('index_speak.html')


@app.route('/upload', methods=['POST'])
def upload_audio():
    audio_data = request.files['audio_data']
    wav_binary.append(audio_data)
    return "sound recorded"


@app.route('/play', methods=['GET'])
def play_audio():
    # Use FFmpeg to decode the binary data of the webm file to raw PCM data
    process = (
        ffmpeg
            .input('pipe:0', format='webm')
            .output('pipe:', format='wav')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    # Feed the binary data to ffmpeg's stdin
    process.stdin.write(wav_binary.popleft())
    process.stdin.close()

    # Read the first few bytes of the WAV header to determine the sample rate and number of channels
    wav_header = process.stdout.read(44)  # WAV header is 44 bytes
    channels = int.from_bytes(wav_header[22:24], byteorder='little')
    sample_rate = int.from_bytes(wav_header[24:28], byteorder='little')

    print(f"Channels: {channels}, Sample Rate: {sample_rate}")

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream with PyAudio for playback
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    output_device_index=6, 
                    output=True)

    chunk_size = 1024

    while True:
        data = process.stdout.read(chunk_size)
        if not data:
            break
        stream.write(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    process.stdout.close()
    process.wait()
    return 'Audio played'


if __name__ == '__main__':
    os.makedirs('recordings', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
