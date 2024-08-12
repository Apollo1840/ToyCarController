import os
import wave
import pyaudio
from pydub import AudioSegment


def play_wav_file(wav_file_path):
    with wave.open(wav_file_path, 'rb') as wf:
        p = pyaudio.PyAudio()

        print(f"sample width: {wf.getsampwidth()}")
        print(f"n channels: {wf.getnchannels()}")
        print(f"framerate: {wf.getframerate()}")

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        # Start the stream
        stream.start_stream()

        CHUNK = 1024
        data = wf.readframes(CHUNK)

        print(f"Playing...from {wav_file_path}")
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        print("finished playing")


def play_webm(file_path, device_name=None):
    # Initialize VLC instance
    instance = vlc.Instance()

    # Create a media player
    player = instance.media_player_new()

    # Set media
    media = instance.media_new(file_path)
    player.set_media(media)

    # Set the desired audio output device if specified
    if device_name:
        # Get the audio output module name (e.g., 'alsa', 'coreaudio', etc.)
        audio_output_module = player.audio_output_device_get()

        # Set the specific audio output device
        player.audio_output_device_set(audio_output_module, device_name)

    # Play the media
    player.play()

    # Keep the program running until the audio finishes
    while player.is_playing():
        pass


def get_webm_info(webm_file_path):
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate',
        '-of', 'json', webm_file_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = json.loads(result.stdout)

    video_frame_rate = None
    audio_sample_rate = None

    for stream in info['streams']:
        if stream['codec_type'] == 'video':
            r_frame_rate = stream['r_frame_rate']
            num, denom = map(int, r_frame_rate.split('/'))
            video_frame_rate = num / denom
        elif stream['codec_type'] == 'audio':
            audio_sample_rate = int(stream['sample_rate'])

    return video_frame_rate, audio_sample_rate


def play_webm_from_binary(webm_binary_data):
    # Use FFmpeg to decode the binary data of the webm file to raw PCM data
    process = (
        ffmpeg
            .input('pipe:0', format='webm')
            .output('pipe:', format='wav')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    # Feed the binary data to ffmpeg's stdin
    process.stdin.write(webm_binary_data)
    process.stdin.close()

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream with PyAudio for playback
    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=48000,
                    output=True)

    chunk_size = 1024

    while True:
        data = process.stdout.read(chunk_size)
        if not data:
            break
        stream.write(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    process.stdout.close()
    process.wait()


if __name__ == "__main__":
    webm_file_path = os.path.join('recordings', 'recorded_audio.webm')
    wav_file_path = os.path.join('recordings', 'recorded_audio.wav')
    wav_file_path2 = os.path.join('recordings', 'output_48000.wav')
    mp4_file_path = os.path.join('recordings', 'recorded_audio.mp4')

    # Convert the audio to WAV format (you can use pydub or similar)
    # sound = AudioSegment.from_file(webm_file_path, format="webm")
    # sound.export(wav_file_path, format="wav")

    play_wav_file(wav_file_path)

    # Example usage: play a file on a specific device
    play_webm(webm_file_path)

    sound = AudioSegment.from_file(webm_file_path, format="webm")
    sound.export(mp4_file_path, format="mp4")

    # Example usage
    video_fps, audio_sample_rate = get_webm_info(webm_file_path)
    print(f"Video Frame Rate: {video_fps} FPS")
    print(f"Audio Sample Rate: {audio_sample_rate} Hz")

    with open(webm_file_path, 'rb') as f:
        webm_binary = f.read()
    play_webm_from_binary(webm_binary)
