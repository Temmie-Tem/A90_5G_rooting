package com.a90.nativeinit.audio;

import android.app.Activity;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.Bundle;
import android.util.Log;

public final class A90AudioRouteStimulusActivity extends Activity {
    public static final String ACTION_PLAY = "com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS";
    private static final String TAG = "A90AudioRouteStimulus";
    private static final int DEFAULT_DURATION_MS = 2000;
    private static final int DEFAULT_SAMPLE_RATE = 48000;
    private static final float DEFAULT_AMPLITUDE = 0.05f;
    private static final double TONE_HZ = 440.0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        final Config config = Config.fromIntent(getIntent());
        Thread worker = new Thread(new Runnable() {
            @Override
            public void run() {
                int rc = 0;
                try {
                    runStimulus(config);
                } catch (Throwable error) {
                    rc = 1;
                    Log.e(TAG, "A90_AUDIO_STIMULUS_ERROR", error);
                } finally {
                    Log.i(TAG, "A90_AUDIO_STIMULUS_FINISH rc=" + rc);
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            finish();
                        }
                    });
                }
            }
        }, "a90-audio-route-stimulus");
        worker.start();
    }

    private void runStimulus(Config config) {
        validate(config);
        AudioManager manager = (AudioManager) getSystemService(AUDIO_SERVICE);
        if (manager != null && config.speakerHint) {
            manager.setMode(AudioManager.MODE_NORMAL);
            manager.setSpeakerphoneOn(true);
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
            int state = track.getState();
            track.release();
            throw new IllegalStateException("AudioTrack not initialized: " + state);
        }

        short[] chunk = makeStereoSineChunk(config.sampleRate, config.amplitude);
        int totalFrames = Math.max(1, config.sampleRate * config.durationMs / 1000);
        int writtenFrames = 0;
        Log.i(TAG, "A90_AUDIO_STIMULUS_BEGIN duration_ms=" + config.durationMs
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
            if (manager != null && config.speakerHint) {
                manager.setSpeakerphoneOn(false);
            }
        }
        Log.i(TAG, "A90_AUDIO_STIMULUS_END frames=" + writtenFrames);
    }

    private static void validate(Config config) {
        if (config.durationMs <= 0 || config.durationMs > 10000) {
            throw new IllegalArgumentException("duration must be 1..10000ms");
        }
        if (config.sampleRate <= 0 || config.sampleRate > 384000) {
            throw new IllegalArgumentException("sample rate out of range");
        }
        if (config.amplitude < 0.0f || config.amplitude > 0.20f) {
            throw new IllegalArgumentException("amplitude must be 0.0..0.20");
        }
    }

    private static short[] makeStereoSineChunk(int sampleRate, float amplitude) {
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
        float amplitude = DEFAULT_AMPLITUDE;
        boolean speakerHint = true;

        static Config fromIntent(Intent intent) {
            Config config = new Config();
            if (intent == null) {
                return config;
            }
            config.durationMs = intent.getIntExtra("duration_ms", DEFAULT_DURATION_MS);
            config.sampleRate = intent.getIntExtra("sample_rate", DEFAULT_SAMPLE_RATE);
            config.amplitude = intent.getFloatExtra("amplitude", DEFAULT_AMPLITUDE);
            config.speakerHint = intent.getBooleanExtra("speaker", true);
            return config;
        }
    }
}
