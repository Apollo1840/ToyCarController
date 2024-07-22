# external pkg
import threading
from flask import Flask, render_template, request, Response, jsonify

# internal pkg
from controller.servo_controller_cv import FaceDetector, TrackableServoController
from controller.motor_controller import MotorController
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
face_detector = FaceDetector()
servo_controller = TrackableServoController(face_detector)
motor_controller = MotorController()
app.config['SECRET_KEY'] = 'secret!'


@app.route('/')
def index():
    return render_template('index2.html')


@socketio.on('move_command')
def handle_move_command(json):
    action = json.get('action')
    if action == 'start':
        direction = json.get('direction')
        motor_controller.move(direction)
    elif action == 'stop':
        motor_controller.stop()

"""
@app.route('/recenter_car')
def recenter_car():
    motor_controller.recenter()
    # Response for when the recenter process starts
    return jsonify(status='recenter_started')


@app.route('/stop_recenter')
def stop_recenter():
    motor_controller.stop_recenter()
    # Response for when the recenter process stops
    return jsonify(status='recenter_stopped')

"""


@app.route('/move_camera')
def move_camera():
    direction = request.args.get('direction')
    servo_controller.move_servo(direction)
    return ('', 204)


@app.route('/toggle_tracking')
def toggle_tracking():
    enabled = request.args.get('enabled', 'false') == 'true'
    servo_controller.set_tracking(enabled)
    return ('', 204)


@app.route('/video_feed')
def video_feed():
    return Response(face_detector.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    threading.Thread(target=face_detector.detect_faces, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
