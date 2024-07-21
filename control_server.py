# external pkg
import threading
from flask import Flask, render_template, request, Response, jsonify

# internal pkg
from controller.servo_controller_cv import FaceDetector, TrackableServoController
from controller.motor_controller import MotorController

app = Flask(__name__)
face_detector = FaceDetector()
servo_controller = TrackableServoController(face_detector)
motor_controller = MotorController()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/move_car')
def move_car():
    direction = request.args.get('direction')
    motor_controller.move(direction)
    return ('', 204)


@app.route('/stop_move_car')
def stop_move_car():
    motor_controller.stop()
    return ('', 204)


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
