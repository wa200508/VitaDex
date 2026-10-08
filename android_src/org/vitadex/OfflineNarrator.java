package org.vitadex;

import android.content.Context;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import java.util.Set;

/** Device speech with an explicitly non-network English voice, initialized on demand. */
public final class OfflineNarrator implements TextToSpeech.OnInitListener {
    private TextToSpeech engine;
    private volatile String state = "loading";
    private volatile String utterance = "";
    private String pending = "";
    private boolean ready = false;
    private boolean closed = false;
    private long generation = 0;

    public OfflineNarrator(Context context) {
        engine = new TextToSpeech(context.getApplicationContext(), this);
    }

    @Override
    public synchronized void onInit(int result) {
        if (closed) return;
        if (result != TextToSpeech.SUCCESS) {
            state = "error:Device speech could not start.";
            return;
        }
        Set<Voice> voices = engine.getVoices();
        Voice selected = null;
        if (voices != null) {
            for (Voice voice : voices) {
                if (!voice.isNetworkConnectionRequired()
                        && "en".equals(voice.getLocale().getLanguage())
                        && (voice.getFeatures() == null
                            || !voice.getFeatures().contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED))) {
                    if (selected == null || voice.getName().compareTo(selected.getName()) < 0) selected = voice;
                }
            }
        }
        if (selected == null || engine.setVoice(selected) != TextToSpeech.SUCCESS) {
            state = "error:Install an offline English voice in Android's text-to-speech settings.";
            return;
        }
        engine.setSpeechRate(0.9f);
        engine.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String id) { }
            @Override public void onDone(String id) {
                synchronized (OfflineNarrator.this) {
                    if (id.equals(utterance)) state = "ready";
                }
            }
            @Override public void onError(String id) {
                synchronized (OfflineNarrator.this) {
                    if (id.equals(utterance)) state = "error:Device speech could not read this text.";
                }
            }
        });
        ready = true;
        state = "ready";
        if (!pending.isEmpty()) playPending();
    }

    public synchronized void speak(String text) {
        if (closed) throw new IllegalStateException("Narrator has closed");
        if (text.length() > TextToSpeech.getMaxSpeechInputLength()) {
            state = "error:This passage is too long to read at once.";
            return;
        }
        pending = text;
        if (ready) playPending();
    }

    private void playPending() {
        utterance = Long.toString(++generation);
        String text = pending;
        pending = "";
        state = "speaking";
        if (engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, utterance) != TextToSpeech.SUCCESS) {
            state = "error:Device speech could not read this text.";
        }
    }

    public String getState() { return state; }

    public synchronized void stop() {
        pending = "";
        utterance = "";
        engine.stop();
        if (ready) state = "ready";
    }

    public synchronized void close() {
        closed = true;
        pending = "";
        utterance = "";
        engine.stop();
        engine.shutdown();
        state = "closed";
    }
}
