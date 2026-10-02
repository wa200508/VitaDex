package org.vitadex;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import org.tensorflow.lite.Interpreter;

/** A bounded, CPU-only runtime for the pinned local ImageNet model. */
public final class LocalClassifier {
    private final Interpreter interpreter;
    private final ByteBuffer input;
    private final ByteBuffer output;

    public LocalClassifier(String modelPath) {
        Interpreter.Options options = new Interpreter.Options().setNumThreads(2);
        interpreter = new Interpreter(new File(modelPath), options);
        if (!Arrays.equals(interpreter.getInputTensor(0).shape(), new int[]{1, 224, 224, 3})
                || !Arrays.equals(interpreter.getOutputTensor(0).shape(), new int[]{1, 1000})) {
            interpreter.close();
            throw new IllegalArgumentException("Unexpected local model tensors");
        }
        input = ByteBuffer.allocateDirect(224 * 224 * 3 * 4).order(ByteOrder.LITTLE_ENDIAN);
        output = ByteBuffer.allocateDirect(1000 * 4).order(ByteOrder.LITTLE_ENDIAN);
    }

    public synchronized float[] predict(byte[] pixels) {
        if (pixels.length != input.capacity()) {
            throw new IllegalArgumentException("Unexpected photo tensor size");
        }
        input.rewind();
        input.put(pixels);
        input.rewind();
        output.rewind();
        interpreter.run(input, output);
        float[] scores = new float[1000];
        for (int i = 0; i < scores.length; i++) {
            scores[i] = output.getFloat(i * 4);
        }
        return scores;
    }

    public synchronized void close() {
        interpreter.close();
    }
}
