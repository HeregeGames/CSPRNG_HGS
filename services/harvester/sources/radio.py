import os
import sys
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
        # Suprime logs de erro verbosos do ALSA/PortAudio para manter a saída limpa
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(sys.stderr.fileno())
        os.dup2(devnull, sys.stderr.fileno())
        
        try:
            audio = pyaudio.PyAudio()
        finally:
            os.dup2(old_stderr, sys.stderr.fileno())
            os.close(devnull)
            os.close(old_stderr)

        stream = None
        try:
            # Tenta encontrar uma taxa de amostragem suportada pelo hardware
            rates_to_try = [self.rate, 48000, 32000, 16000, 8000]
            
            # Tenta obter a taxa padrão do dispositivo para priorizá-la
            try:
                device_info = audio.get_default_input_device_info()
                default_rate = int(device_info.get('defaultSampleRate', 0))
                if default_rate > 0 and default_rate not in rates_to_try:
                    rates_to_try.insert(0, default_rate)
            except Exception:
                pass

            for rate in rates_to_try:
                try:
                    stream = audio.open(format=self.format, channels=self.channels,
                                        rate=rate, input=True,
                                        frames_per_buffer=self.chunk)
                    self.rate = rate
                    break
                except Exception:
                    continue

            if not stream:
                raise RuntimeError("Não foi possível abrir o stream de áudio com nenhuma taxa suportada.")

            self.logger.debug(f"Capturing audio sample at {self.rate}Hz...")
            frames = []
            num_chunks = int(self.rate / self.chunk * self.record_seconds)
            for _ in range(0, max(1, num_chunks)):
                # exception_on_overflow=False evita crashes se o sistema estiver lento
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)

            self.logger.info("Audio sample captured successfully.", extra={'event': 'audio_capture_success'})
            return b''.join(frames)

        except Exception as e:
            self.logger.error(f"Could not capture audio. Error: {e}", extra={'event': 'audio_capture_failure'})
            return None
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            audio.terminate()
