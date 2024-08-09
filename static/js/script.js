let moveCarInterval;
let moveCameraInterval;
let isTracking = false;
let isRecentering = false;
const socket = io();

function startMovingCar(direction) {
    socket.emit('move_command', {direction: direction, action: 'start'});
}

function stopMovingCar() {
    socket.emit('move_command', {action: 'stop'});
}

function startRecenter() {
    socket.emit('recenter_command', {action: 'start'});
}

function stopRecenter() {
    socket.emit('recenter_command', {action: 'stop'});
}

// Logic to control the movement of the camera
function startMovingCamera(direction) {
    if (!isTracking) {
        fetch(`/move_camera?direction=${direction}`);
        moveCameraInterval = setInterval(() => {
            fetch(`/move_camera?direction=${direction}`);
        }, 100); // Adjust the interval as needed
    }
}

function stopMovingCamera() {
    clearInterval(moveCameraInterval);
}

function toggleTracking() {
    isTracking = !isTracking;
    const buttons = document.querySelectorAll('.camera-control-buttons button');
    buttons.forEach(button => {
        if (button.id !== 'track-button') {
            button.classList.toggle('disabled-button', isTracking);
            button.disabled = isTracking;
        }
    });
    document.getElementById('track-button').classList.toggle('tracking-mode', isTracking);

    fetch(`/toggle_tracking?enabled=${isTracking}`);
}

// Ensure that movement stops if the mouse or touch leaves the button
document.querySelectorAll('button').forEach(button => {
    button.onmouseleave = () => {
        stopMovingCar();
        stopMovingCamera();
    };
    button.ontouchcancel = () => {
        stopMovingCar();
        stopMovingCamera();
    };
});