let isListening = false;
let audioBufferQueue = [];
let audioContext;
let source;

document.getElementById('listenBtn').onclick = function() {
    isListening = !isListening;
    document.getElementById('listenBtn').innerText = isListening ? 'Stop' : 'Listen';
    document.getElementById('recordingIndicator').style.display = isListening ? 'inline-block' : 'none';

    fetch('/listen', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
        console.log(data);
        if (isListening) {
            fetchNextAudio();
        } else {
            if (source) {
                source.stop();
            }
        }
    })
        .catch(error => console.error('Error:', error));
};

function fetchNextAudio() {
    fetch('/get_audio')
        .then(response => {
        if (response.headers.get("Content-Type") === "text/plain") {
            return response.text();
        } else {
            return response.arrayBuffer();
        }
    })
        .then(data => {
        if (typeof data === "string" && data === "Empty") {
            console.log("Empty audio buffer");
        } else {
            audioBufferQueue.push(data);
            if (audioBufferQueue.length === 1) {
                playAudio();
            }
        }
    })
        .catch(error => console.error('Error:', error));
}

function playAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioBufferQueue.length === 0 || !isListening) {
        return;
    }
    const arrayBuffer = audioBufferQueue.shift();
    audioContext.decodeAudioData(arrayBuffer, (audioBuffer) => {
        source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start(0);
        source.onended = () => {
            if (isListening) {
                playAudio();
                fetchNextAudio();
            }
        };
    }, (error) => {
        console.error('Error decoding audio data:', error);
    });
}
