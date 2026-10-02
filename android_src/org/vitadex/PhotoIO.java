package org.vitadex;

import android.content.Context;
import android.net.Uri;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;

/** Copy a user-selected document into private app storage without storage permission. */
public final class PhotoIO {
    public static void copyUri(Context context, String uri, String destination) throws IOException {
        File target = new File(destination);
        try (InputStream source = context.getContentResolver().openInputStream(Uri.parse(uri));
                FileOutputStream output = new FileOutputStream(target)) {
            if (source == null) throw new IOException("The selected photo is unavailable");
            byte[] buffer = new byte[8192];
            long total = 0;
            int count;
            while ((count = source.read(buffer)) != -1) {
                total += count;
                if (total > 32L * 1024 * 1024) throw new IOException("Photo exceeds 32 MB");
                output.write(buffer, 0, count);
            }
        } catch (IOException error) {
            target.delete();
            throw error;
        }
    }
}
