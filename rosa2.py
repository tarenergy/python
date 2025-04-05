def generate_pink_noise(samples, sample_rate, min_freq, max_freq):
    """Erzeugt rosa Rauschen im Frequenzbereich zwischen min_freq und max_freq."""
    noise = np.random.randn(samples)
    fft_noise = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(samples, 1 / sample_rate)
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    fft_noise[~mask] = 0  # Frequenzen außerhalb des Bereichs entfernen
    pink_noise = np.fft.irfft(fft_noise)
    pink_noise /= np.max(np.abs(pink_noise))  # Normalisieren
    return pink_noise * 0.5