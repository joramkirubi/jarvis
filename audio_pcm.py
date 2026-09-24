"""Convert microphone PCM to the agent's 16 kHz mono format."""
import numpy as np
from scipy.signal import firwin, lfilter

class InputPCM:
    def __init__(self, rate=16000, channels=1):
        if rate not in (16000, 48000) or channels not in (1, 2):
            raise ValueError('Use 16000 or 48000 Hz and 1 or 2 channels')
        self.rate, self.channels = rate, channels
        self.taps = firwin(63, 7000, fs=48000)
        self.state = np.zeros(62)
        self.offset = 0

    def convert(self, data):
        samples = np.frombuffer(data, dtype='<i2').reshape(-1, self.channels).astype(np.float64).mean(axis=1)
        if self.rate == 48000:
            samples, self.state = lfilter(self.taps, [1.0], samples, zi=self.state)
            start = (-self.offset) % 3
            self.offset = (self.offset + len(samples)) % 3
            samples = samples[start::3]
        return np.clip(np.rint(samples), -32768, 32767).astype('<i2').tobytes()
