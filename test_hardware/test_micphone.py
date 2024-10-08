import numpy as np
import os
import argparse
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import wave
import pyaudio


def list_audio_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            print(f"Device ID {i} - {device_info.get('name')}")
    p.terminate()


def test_microphone(device_index, duration=1):
    p = pyaudio.PyAudio()

    device_info = p.get_device_info_by_index(device_index)
    print(device_info)

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=4096)  # Increased buffer size

    print(f"Recording from device {device_index} for {duration} seconds...")

    frames = []
    try:
        for _ in range(0, int(44100 / 1024 * duration)):
            data = stream.read(1024, exception_on_overflow=False)  # Handle overflow
            frames.append(data)
    except IOError as e:
        print(f"Error recording: {e}")

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Check if data was captured
    if len(frames) > 0:
        print("Audio data captured successfully.")
    else:
        print("Failed to capture audio data.")


def try_microphone(filename, frames_per_buffer=8192):
    global frames
    # Define parameters
    FORMAT = pyaudio.paInt16  # Sampling format
    CHANNELS = 1  # Mono
    RATE = 44100  # Sampling rate
    RECORD_SECONDS = 10  # Duration to record

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream using callback
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=frames_per_buffer,
                    stream_callback=callback)

    print("Recording started...")

    # Start the stream
    stream.start_stream()

    # Record for the specified duration
    time.sleep(RECORD_SECONDS)

    print("Recording finished.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


# Play back the recorded audio
def play_audio(filename, chunk_size=8192):
    with wave.open(filename, 'rb') as wf:
        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        data = wf.readframes(chunk_size)

        while data:
            stream.write(data)
            data = wf.readframes(chunk_size)

        stream.stop_stream()
        stream.close()
        p.terminate()


def play_audio_v(filename, chunk_size=8192, volume=2.0):
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


# Function to plot the waveform
def plot_waveform(filename):
    wf = wave.open(filename, 'rb')
    n_channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    framerate = wf.getframerate()
    n_frames = wf.getnframes()
    audio_data = wf.readframes(n_frames)
    wf.close()

    # Convert audio data to numpy array
    audio_data = np.frombuffer(audio_data, dtype=np.int16)

    # Create time array
    time_array = np.linspace(0, n_frames / framerate, num=n_frames)

    # Plot waveform
    plt.figure(figsize=(12, 6))
    plt.plot(time_array, audio_data)
    plt.title("Waveform of Recorded Audio")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.show()


def play_audio_from_frames(frames, format, channels, rate):
    p = pyaudio.PyAudio()
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    output=True)

    for frame in frames:
        time.sleep(0.1)
        stream.write(frame)

    stream.stop_stream()
    stream.close()
    p.terminate()
    # Callback function to capture audio


def callback(in_data, frame_count, time_info, status):
    frames.append(in_data)
    return (in_data, pyaudio.paContinue)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio recording and playback script.")
    parser.add_argument("--chunk", type=int, default=8192, help="Buffer size for audio recording and playback.")
    parser.add_argument("--output", type=str, default="output.wav", help="Filename for the recorded audio.")
    args = parser.parse_args()

    WAVE_OUTPUT_FILENAME = os.path.join("recordings", args.output)  # Output file name

    print("Listing available audio devices:")
    list_audio_devices()

    device_index = int(input("Enter the device index to test: "))
    test_microphone(device_index)

    print("try_recording...")
    frames = []
    try_microphone(WAVE_OUTPUT_FILENAME, frames_per_buffer=args.chunk)

    print("Playing back the recorded audio...")
    play_audio(WAVE_OUTPUT_FILENAME, chunk_size=args.chunk)
    play_audio_v(WAVE_OUTPUT_FILENAME, chunk_size=args.chunk)

    exit()

    print("Plotting the waveform of the recorded audio...")
    plot_waveform(WAVE_OUTPUT_FILENAME)

    # Play back the recorded audio directly from frames
    print("Playing back the recorded audio...")
    play_audio_from_frames(frames, FORMAT, CHANNELS, RATE)

    print(frames[0])
    print(len(frames))
