import numpy as np
import matplotlib.pyplot as plt
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


def test_microphone(device_index, duration=5):
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


# Function to plot the waveform
def plot_waveform(filename):
    with wave.open(filename, 'rb') as wf:
        # n_channels = wf.getnchannels()
        # sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)

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


# Play back the recorded audio
def play_audio(filename):
    with wave.open(filename, 'rb') as wf:
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()
    p.terminate()


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
    print("Listing available audio devices:")
    list_audio_devices()

    device_index = int(input("Enter the device index to test: "))
    test_microphone(device_index)

    # Define parameters
    CHUNK = 8192  # Increased buffer size
    FORMAT = pyaudio.paInt16  # Sampling format
    CHANNELS = 1  # Mono
    RATE = 44100  # Sampling rate
    RECORD_SECONDS = 10  # Duration to record
    WAVE_OUTPUT_FILENAME = "output.wav"  # Output file name

    frames = []

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream using callback
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    print("Recording started...")
    stream.start_stream()
    time.sleep(RECORD_SECONDS)
    stream.stop_stream()
    print("Recording finished.")

    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        wf.writeframes(b''.join(frames))

    print("Plotting the waveform of the recorded audio...")
    plot_waveform(WAVE_OUTPUT_FILENAME)

    # Play back the recorded audio directly from frames
    print("Playing back the recorded audio...")
    play_audio_from_frames(frames, FORMAT, CHANNELS, RATE)

    print("Playing back the recorded audio...")
    play_audio(WAVE_OUTPUT_FILENAME)
