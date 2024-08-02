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
// let shouldContinue = false;


function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
        shouldContinue = true;
        //console.log("got stream");

        function recordAndSend() {

            if (!shouldContinue) {
                document.getElementById("log").textContent = "stopped recordAndSend";
                return;};

            document.getElementById("log").textContent = "running recordAndSend";
            setTimeout(() => {
                recordAndSend();
            }, 1000);
            /*
            let mediaRecorder;
            let chunks = [];

            try {
                console.log("Attempting to set MediaRecorder...");
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

                console.log("MediaRecorder is successfully set.");
                console.log("Configuring the MediaRecorder...");

                mediaRecorder.ondataavailable = event => {
                    console.log("pushing chunks...");
                    chunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    console.log("media recorder going to close, uploading the audio...");
                    const audioBlob = new Blob(chunks, { type: 'audio/webm' });

                    const formData = new FormData();
                    formData.append('audio_data', audioBlob);

                    fetch('/upload_audio', {
                        method: 'POST',
                        body: formData
                    }).then(response => {
                        console.log('Audio uploaded:', response.status);
                        if (shouldContinue) {
                            console.log("--------------------------------");
                            recordAndSend(); // Automatically start the next recording
                        }
                    });
                };

                console.log("MediaRecorder successfully configured");
                console.log("Starting the recording...");

                mediaRecorder.start(250);

                // Stop the recording after 250ms
                setTimeout(() => {
                    mediaRecorder.stop();
                }, 1000);

            } catch (error) {
                console.error("Failed to set or configure MediaRecorder: ", error);
                alert("An error occurred while setting up the MediaRecorder. Please check the console for details.");
            }
            */
        }

        // Start the first recording
        recordAndSend();

        // Start the server-side process for playing audio
        fetch('/speak', { method: 'POST' })
            .then(response => response.json())
        //.then(data => console.log(data.status));
    })
        .then()
        .catch(error => {
        console.error("Error accessing media devices: ", error);
        alert("An error occurred while accessing your microphone. Please check your permissions and try again.");
    });
}

function stopRecording() {
    // console.log("Stopping recording...");
    shouldContinue = false;

    // Stop the server-side process
    fetch('/speak', { method: 'POST' })
        .then(response => response.json())
    //.then(data => console.log(data.status));
}

function toggleRecording() {
    //console.log("clicked button");

    const recordButton = document.getElementById("recordButton");
    // if (!recordButton) {
    //    console.error("recordButton not found!");
    //    return;
    //}

    if (!isRecording) {
        // console.log("ready to start");
        startRecording();
        // const recordButton = document.getElementById("recordButton");
        recordButton.textContent = "Stop";
        recordButton.classList.add('redDot');
        // console.log("button text changed");
    } else {
        stopRecording();
        // const recordButton = document.getElementById("recordButton");
        recordButton.textContent = "Speak";
        recordButton.classList.remove('redDot');

    }
    isRecording = !isRecording;
}
