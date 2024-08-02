// Override console.log and console.error to display messages on the webpage
console.log = function(message) {
    document.body.innerHTML += '<p>' + message + '</p>';
    //document.body.offsetHeight; // Force a reflow/repaint
};

console.error = function(message) {
    document.body.innerHTML += '<p style="color: red;">' + message + '</p>';
    //document.body.offsetHeight; // Force a reflow/repaint
};

window.onerror = function(message, source, lineno, colno, error) {
    document.body.innerHTML += `<p style="color: red;">Error: ${message} at ${source}:${lineno}:${colno}</p>`;
};


/*
// Check for browser support of getUserMedia and MediaRecorder
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Your browser does not support audio recording. Please use a modern browser.');
}

if (!MediaRecorder.isTypeSupported('audio/webm')) {
    console.error("audio/webm is not supported on this browser.");

    // Call the function to check supported audio formats
    checkSupportedMimeTypes();
}

function checkSupportedMimeTypes() {
    const mimeTypes = [
        'audio/webm',
        'audio/ogg',
        'audio/wav',
        'audio/mpeg',
        'audio/mp4',
        'audio/x-matroska',
        'audio/aac'
    ];

    mimeTypes.forEach(mimeType => {
        if (MediaRecorder.isTypeSupported(mimeType)) {
            console.log(`Supported MIME type: ${mimeType}`);
        } else {
            console.error(`Not supported MIME type: ${mimeType}`);
        }
    });
}
*/

// Add event listeners for both click and touchstart
document.getElementById("recordButton").addEventListener('click', function(event) {
    event.preventDefault();
    toggleRecording();
});

document.getElementById("recordButton").addEventListener('touchstart', function(event) {
    event.preventDefault(); // Prevent the default touch behavior
    toggleRecording();
});

let isRecording = false;
let shouldContinue = false;


function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
        shouldContinue = true;
        document.getElementById("shouldContinue").textContent = "shouldContinue:true";

        function recordAndSend() {
            document.getElementById("log").textContent = "running recordAndSend";

            let mediaRecorder;
            let audioChunks = [];

            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorder.ondataavailable = event => {audioChunks.push(event.data);};
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio_data', audioBlob);

                fetch('/upload_audio', {
                    method: 'POST',
                    body: formData
                })

                if (shouldContinue) {
                    recordAndSend();
                } else {
                    document.getElementById("log").textContent = "stopped recordAndSend";
                };
            };
            mediaRecorder.start(250);
            setTimeout(() => {
                mediaRecorder.stop();
            }, 1000);
        }

        recordAndSend();

        fetch('/speak', { method: 'POST' }).then(response => response.json())})
}

function stopRecording() {
    shouldContinue = false;
    document.getElementById("shouldContinue").textContent = "shouldContinue:false";

    // Stop the server-side process
    fetch('/speak', { method: 'POST' })
        .then(response => response.json())
}

function toggleRecording() {
    const recordButton = document.getElementById("recordButton");
    if (!isRecording) {
        recordButton.textContent = "Stop";
        recordButton.classList.add('redDot');
        startRecording();
    } else {
        recordButton.textContent = "Speak";
        recordButton.classList.remove('redDot');
        stopRecording();
    }
    isRecording = !isRecording;
}
