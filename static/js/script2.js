let moveCarInterval;
let moveCameraInterval;
let isTracking = false;
let isRecentering = false;
let isListening = false;
let isSpeaking = false;

let audioContext;
let source;

const socket = io();

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


document.getElementById("speakBtn").onclick = function() {
    isSpeaking = !isSpeaking;
    document.getElementById('speakBtn').innerText = isSpeaking ? 'Stop' : 'Speak';
    document.getElementById('speakingIndicator').style.display = isSpeaking ? 'inline-block' : 'none';

    console.log("clicked speak button")
    fetch('/speak', {method: 'POST'})
        .then(response => {console.log("get response"); response.json()})
        .then(data => {console.log(data);
        if (isSpeaking) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {sendNextAudio(stream);})
        }
    }).catch(error => console.error('Error:', error));
}


document.getElementById('listenBtn').onclick = function() {
    isListening = !isListening;
    document.getElementById('listenBtn').innerText = isListening ? 'Stop' : 'Listen';
    document.getElementById('recordingIndicator').style.display = isListening ? 'inline-block' : 'none';

    console.log("clicked listen button")
    fetch('/listen', {method: 'POST'})
        .then(response => response.json())
        .then(data => {console.log(data);
        if (isListening) {fetchNextAudio();}
        else {if (source) {source.stop();}}
    }).catch(error => console.error('Error:', error));
}

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


function fetchNextAudio() {
    fetch('/get_audio')
        .then(response => {
        if (response.headers.get("Content-Type") === "text/plain") {
            return response.text();
        } else {
            return response.arrayBuffer();
        }})
        .then(data => {
        if (typeof data === "string" && data === "Empty") {
            console.log("Empty audio buffer");
        } else {
            const arrayBuffer = data;
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (isListening){audioContext.decodeAudioData(arrayBuffer,
                (audioBuffer) => {
                    source = audioContext.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(audioContext.destination);
                    source.start(0);
                    source.onended = () => {if (isListening) {fetchNextAudio();}};
                },
                (error) => {console.error('Error decoding audio data:', error);}
            );}

        }}
    ).catch(error => console.error('Error:', error));
}


function sendNextAudio(stream) {

    let mediaRecorder;
    let audioChunks = [];

    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    mediaRecorder.ondataavailable = event => {audioChunks.push(event.data);};
    mediaRecorder.onstop = () => {
        setTimeout(() => {
            if (isSpeaking) {
                sendNextAudio(stream);
            };
        }, 0)

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio_data', audioBlob);
        fetch('/upload_audio', {
            method: 'POST',
            body: formData
        })
    };
    mediaRecorder.start(250);
    setTimeout(() => {
        mediaRecorder.stop();
    }, 1000);
}
