import os
import wave
import numpy as np
import pyaudio
import argparse


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


def play_wav_file_v(filename, chunk_size=8192, volume=2.0):
    with wave.open(filename, 'rb') as wf:
        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(chunk_size)

        while data:
            # Convert byte data to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)

            # Amplify the audio data by the volume factor
            audio_data = np.int16(audio_data * volume)

            # Convert numpy array back to bytes
            data = audio_data.tobytes()

            stream.write(data)
            data = wf.readframes(chunk_size)

        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio recording and playback script.")
    parser.add_argument("--output", type=str, default="output.wav", help="Filename for the recorded audio.")
    args = parser.parse_args()

    wav_file_path = os.path.join("recordings", args.output)  # Output file name
    play_wav_file(wav_file_path)
    play_wav_file_v(wav_file_path, volume=5.0)
