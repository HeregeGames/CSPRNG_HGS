import pyaudio
from .base import BaseSource

class Radio(BaseSource):
    def __init__(self):
        super().__init__()
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.record_seconds = 0.1  # Captura muito curta, apenas para ruído
        self.interval = 5  # 5 segundos

    def get_entropy(self) -> bytes | None:
        audio = pyaudio.PyAudio()
        try:
            stream = audio.open(format=self.format, channels=self.channels,
                                rate=self.rate, input=True,
                                frames_per_buffer=self.chunk)

            self.logger.debug("Capturing audio sample...")
            frames = []
            # Calcula o número de chunks a ler
            num_chunks = int(self.rate / self.chunk * self.record_seconds)
            for _ in range(0, max(1, num_chunks)): # Garante ler pelo menos 1 chunk
                data = stream.read(self.chunk)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            self.logger.info("Audio sample captured successfully.", extra={'event': 'audio_capture_success'})
            return b''.join(frames)

        except Exception as e:
            self.logger.error(f"Could not capture audio. Is a microphone connected or available? Error: {e}", extra={'event': 'audio_capture_failure'})
            return None
        finally:
            audio.terminate()
