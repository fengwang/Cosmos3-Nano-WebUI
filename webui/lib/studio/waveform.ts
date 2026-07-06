// Waveform peak extraction (ACD: pure Calculation; inspect). The Action of decoding audio
// (AudioContext.decodeAudioData) lives in the Waveform component; this turns raw samples into the
// normalized bar heights the canvas draws, so the math is unit-testable without Web Audio.

/** Downsample mono samples to `buckets` absolute-peak values in [0,1]. Empty input / buckets ≤ 0 → []. */
export function downsamplePeaks(samples: Float32Array | number[], buckets: number): number[] {
  const n = samples.length;
  if (buckets <= 0 || n === 0) return [];
  const size = Math.ceil(n / buckets);
  const peaks: number[] = [];
  for (let start = 0; start < n; start += size) {
    const end = Math.min(start + size, n);
    let peak = 0;
    for (let i = start; i < end; i++) {
      const v = Math.abs(samples[i]);
      if (v > peak) peak = v;
    }
    peaks.push(peak > 1 ? 1 : peak);
  }
  return peaks;
}
