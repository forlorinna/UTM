package my.utmkl.realworld;

import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.webkit.WebView;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.OutputStream;

@CapacitorPlugin(name = "SceneBridge")
public class SceneBridge extends Plugin {
    @PluginMethod
    public void device(PluginCall call) {
        JSObject result = new JSObject();
        result.put("sdk", Build.VERSION.SDK_INT);
        result.put("abi", String.join(",", Build.SUPPORTED_ABIS));
        var provider = WebView.getCurrentWebViewPackage();
        result.put("webView", provider == null ? "unknown" : provider.versionName);
        var prefs = getActivity().getPreferences(Context.MODE_PRIVATE);
        result.put("safe", prefs.getBoolean("safeNextLoad", false));
        prefs.edit().remove("safeNextLoad").apply();
        call.resolve(result);
    }

    @PluginMethod
    public void report(PluginCall call) {
        String event = call.getString("event", "");
        Log.i("UTMKL-Scene", event.substring(0, Math.min(360, event.length())));
        call.resolve();
    }

    @PluginMethod
    public void savePhoto(PluginCall call) {
        String encoded = call.getString("base64", "");
        if (encoded.isEmpty() || encoded.length() > 32_000_000) {
            call.reject("PNG size is invalid");
            return;
        }
        var resolver = getContext().getContentResolver();
        Uri uri = null;
        try {
            byte[] bytes = Base64.decode(encoded, Base64.DEFAULT);
            if (bytes.length < 8 || bytes[0] != (byte) 0x89 || bytes[1] != 0x50 || bytes[2] != 0x4e || bytes[3] != 0x47) {
                call.reject("Invalid PNG");
                return;
            }
            ContentValues values = new ContentValues();
            values.put(MediaStore.Images.Media.DISPLAY_NAME, "UTMKL-" + System.currentTimeMillis() + ".png");
            values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
            values.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/UTMKL");
            values.put(MediaStore.Images.Media.IS_PENDING, 1);
            uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
            if (uri == null) throw new IllegalStateException("Unable to create photo");
            try (OutputStream output = resolver.openOutputStream(uri)) {
                if (output == null) throw new IllegalStateException("Unable to write photo");
                output.write(bytes);
            }
            values.clear();
            values.put(MediaStore.Images.Media.IS_PENDING, 0);
            resolver.update(uri, values, null, null);
            JSObject result = new JSObject();
            result.put("uri", uri.toString());
            call.resolve(result);
        } catch (Exception error) {
            if (uri != null) resolver.delete(uri, null, null);
            call.reject("Unable to save photo", error);
        }
    }
}
