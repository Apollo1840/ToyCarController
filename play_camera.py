from flask import Flask, Response
from picamera import PiCamera
from io import BytesIO

app = Flask(__name__)
camera = PiCamera()

def generate_frames():
    stream = BytesIO()
    for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
        stream.seek(0)
        frame = stream.read()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        stream.seek(0)
        stream.truncate()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return "<h1>Raspberry Pi Camera Stream</h1><img src='/video_feed'>"

if __name__ == '__main__':
    camera.start_preview()
    app.run(host='0.0.0.0', port=5001)
