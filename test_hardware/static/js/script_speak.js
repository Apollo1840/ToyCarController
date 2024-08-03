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
                setTimeout(() => {
                    if (shouldContinue) {
                        recordAndSend();
                    } else {
                        document.getElementById("log").textContent = "stopped recordAndSend";
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
