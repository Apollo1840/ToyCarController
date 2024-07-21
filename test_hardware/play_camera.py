from flask import Flask, Response
import cv2

app = Flask(__name__)


def generate_frames():
    camera = cv2.VideoCapture(0)  # 0表示第一个USB摄像头
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return "<h1>USB Camera Stream</h1><img src='/video_feed'>"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
