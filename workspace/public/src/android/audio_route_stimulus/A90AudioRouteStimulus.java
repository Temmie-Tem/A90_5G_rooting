import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;

public final class A90AudioRouteStimulus {
    private static final int DEFAULT_DURATION_MS = 2000;
    private static final int DEFAULT_SAMPLE_RATE = 48000;
    private static final double DEFAULT_AMPLITUDE = 0.05;
    private static final double TONE_HZ = 440.0;

    private A90AudioRouteStimulus() {
    }

    public static void main(String[] args) throws Exception {
        Config config = Config.parse(args);
        run(config);
    }

    private static void run(Config config) {
        if (config.durationMs <= 0 || config.durationMs > 10000) {
            throw new IllegalArgumentException("duration must be 1..10000ms");
        }
        if (config.sampleRate <= 0 || config.sampleRate > 384000) {
            throw new IllegalArgumentException("sample rate out of range");
        }
        if (config.amplitude < 0.0 || config.amplitude > 0.20) {
            throw new IllegalArgumentException("amplitude must be 0.0..0.20");
        }

        AudioAttributes attributes = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .build();
        AudioFormat format = new AudioFormat.Builder()
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                .setSampleRate(config.sampleRate)
                .build();
        int minBuffer = AudioTrack.getMinBufferSize(
                config.sampleRate,
                AudioFormat.CHANNEL_OUT_STEREO,
                AudioFormat.ENCODING_PCM_16BIT);
        if (minBuffer <= 0) {
            throw new IllegalStateException("AudioTrack min buffer failed: " + minBuffer);
        }

        AudioTrack track = new AudioTrack(
                attributes,
                format,
                Math.max(minBuffer, config.sampleRate / 10 * 4),
                AudioTrack.MODE_STREAM,
                AudioManager.AUDIO_SESSION_ID_GENERATE);
        if (track.getState() != AudioTrack.STATE_INITIALIZED) {
            track.release();
            throw new IllegalStateException("AudioTrack not initialized: " + track.getState());
        }
        short[] chunk = makeStereoSineChunk(config.sampleRate, config.amplitude);
        int totalFrames = Math.max(1, config.sampleRate * config.durationMs / 1000);
        int writtenFrames = 0;

        System.out.println("A90_AUDIO_STIMULUS_BEGIN"
                + " duration_ms=" + config.durationMs
                + " sample_rate=" + config.sampleRate
                + " amplitude=" + config.amplitude
                + " speaker_hint=" + config.speakerHint);
        track.play();
        try {
            while (writtenFrames < totalFrames) {
                int framesRemaining = totalFrames - writtenFrames;
                int framesThisWrite = Math.min(framesRemaining, chunk.length / 2);
                int samplesToWrite = framesThisWrite * 2;
                int result = track.write(chunk, 0, samplesToWrite);
                if (result < 0) {
                    throw new IllegalStateException("AudioTrack write failed: " + result);
                }
                if (result == 0) {
                    throw new IllegalStateException("AudioTrack write made no progress");
                }
                writtenFrames += result / 2;
            }
        } finally {
            track.stop();
            track.release();
        }
        System.out.println("A90_AUDIO_STIMULUS_END frames=" + writtenFrames);
    }

    private static short[] makeStereoSineChunk(int sampleRate, double amplitude) {
        int frames = Math.max(256, sampleRate / 20);
        short[] data = new short[frames * 2];
        double scale = amplitude * Short.MAX_VALUE;
        for (int frame = 0; frame < frames; frame++) {
            double phase = (2.0 * Math.PI * TONE_HZ * frame) / sampleRate;
            short sample = (short) Math.round(Math.sin(phase) * scale);
            data[frame * 2] = sample;
            data[frame * 2 + 1] = sample;
        }
        return data;
    }

    private static final class Config {
        int durationMs = DEFAULT_DURATION_MS;
        int sampleRate = DEFAULT_SAMPLE_RATE;
        double amplitude = DEFAULT_AMPLITUDE;
        boolean speakerHint = false;

        static Config parse(String[] args) {
            Config config = new Config();
            for (int index = 0; index < args.length; index++) {
                String arg = args[index];
                if ("--speaker".equals(arg)) {
                    config.speakerHint = true;
                } else if ("--duration-ms".equals(arg)) {
                    config.durationMs = Integer.parseInt(requireValue(args, ++index, arg));
                } else if ("--sample-rate".equals(arg)) {
                    config.sampleRate = Integer.parseInt(requireValue(args, ++index, arg));
                } else if ("--amplitude".equals(arg)) {
                    config.amplitude = Double.parseDouble(requireValue(args, ++index, arg));
                } else {
                    throw new IllegalArgumentException("unknown argument: " + arg);
                }
            }
            return config;
        }

        private static String requireValue(String[] args, int index, String arg) {
            if (index >= args.length) {
                throw new IllegalArgumentException("missing value for " + arg);
            }
            return args[index];
        }
    }
}
