package my.utmkl.realworld;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.util.Base64;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Collections;
import java.util.Map;

public final class CampusActivity extends Activity {
    private static final String ORIGIN = "https://utmkl.local";
    private static final int PICK_SPLAT = 101;
    private static final Map<String, String> ASSET_HEADER = Collections.singletonMap(
        "Cache-Control", "no-store");
    private WebView view;
    private ValueCallback<Uri[]> selection;

    @Override
    @SuppressLint("SetJavaScriptEnabled")
    public void onCreate(Bundle state) {
        super.onCreate(state);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        view = new WebView(this);
        view.setBackgroundColor(0xff13241a);
        view.setOverScrollMode(View.OVER_SCROLL_NEVER);
        WebSettings settings = view.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setBlockNetworkLoads(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportZoom(false);
        view.setWebViewClient(new LocalAssets());
        view.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> result,
                                              FileChooserParams params) {
                if (selection != null) selection.onReceiveValue(null);
                selection = result;
                Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT)
                    .addCategory(Intent.CATEGORY_OPENABLE)
                    .setType("*/*");
                try {
                    startActivityForResult(picker, PICK_SPLAT);
                } catch (android.content.ActivityNotFoundException error) {
                    selection.onReceiveValue(null);
                    selection = null;
                }
                return true;
            }
        });
        view.addJavascriptInterface(new PhotoStorage(), "CampusAndroid");
        setContentView(view);
        immersive();
        view.loadUrl(ORIGIN + "/index.html");
    }

    @Override
    protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_SPLAT && selection != null) {
            selection.onReceiveValue(result == RESULT_OK && data != null && data.getData() != null
                ? new Uri[]{data.getData()} : null);
            selection = null;
        }
    }

    private void immersive() {
        if (Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.systemBars());
                controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
        }
    }

    @Override
    public void onWindowFocusChanged(boolean focused) {
        super.onWindowFocusChanged(focused);
        if (focused) immersive();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (view != null) view.onResume();
    }

    @Override
    protected void onPause() {
        if (view != null) view.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (view != null) {
            view.removeJavascriptInterface("CampusAndroid");
            view.destroy();
        }
        super.onDestroy();
    }

    private static boolean isLocal(Uri url) {
        return "https".equals(url.getScheme()) && "utmkl.local".equals(url.getHost())
            && url.getPort() == -1 && url.getUserInfo() == null;
    }

    private final class LocalAssets extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView webView, WebResourceRequest request) {
            return !isLocal(request.getUrl());
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView webView, WebResourceRequest request) {
            Uri url = request.getUrl();
            String path = url.getPath();
            if (!isLocal(url) || path == null || !path.matches("/[A-Za-z0-9_./-]+") || path.contains("..")) {
                return missing();
            }
            String mime = mimeFor(path);
            boolean text = mime.startsWith("text/") || mime.equals("application/json")
                || mime.equals("application/javascript");
            try {
                return new WebResourceResponse(mime, text ? "UTF-8" : null, 200, "OK",
                    ASSET_HEADER, getAssets().open("world" + path));
            } catch (IOException error) {
                return missing();
            }
        }

        private WebResourceResponse missing() {
            return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
        }

        private String mimeFor(String path) {
            if (path.endsWith(".html")) return "text/html";
            if (path.endsWith(".js")) return "application/javascript";
            if (path.endsWith(".css")) return "text/css";
            if (path.endsWith(".json")) return "application/json";
            if (path.endsWith(".wasm")) return "application/wasm";
            if (path.endsWith(".glb")) return "model/gltf-binary";
            if (path.endsWith(".png")) return "image/png";
            if (path.endsWith(".jpg")) return "image/jpeg";
            if (path.endsWith(".txt")) return "text/plain";
            return "application/octet-stream";
        }
    }

    public final class PhotoStorage {
        @JavascriptInterface
        public String savePhoto(String name, String image) {
            String prefix = "data:image/jpeg;base64,";
            if (name == null || !name.matches("UTMKL-[0-9TZ-]+\\.jpg") || image == null
                || image.length() > 32_000_000 || !image.startsWith(prefix)) return "Invalid photo";
            Uri result = null;
            try {
                byte[] bytes = Base64.decode(image.substring(prefix.length()), Base64.DEFAULT);
                if (bytes.length < 4 || bytes[0] != (byte) 0xff || bytes[1] != (byte) 0xd8) {
                    return "Invalid JPEG photo";
                }
                ContentValues values = new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
                values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                values.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/UTMKL");
                values.put(MediaStore.Images.Media.IS_PENDING, 1);
                result = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                if (result == null) return "Could not create photo";
                try (OutputStream stream = getContentResolver().openOutputStream(result)) {
                    if (stream == null) throw new IOException("No output stream");
                    stream.write(bytes);
                }
                values.clear();
                values.put(MediaStore.Images.Media.IS_PENDING, 0);
                getContentResolver().update(result, values, null, null);
                return "ok";
            } catch (IOException | RuntimeException error) {
                if (result != null) {
                    try { getContentResolver().delete(result, null, null); }
                    catch (RuntimeException ignored) { }
                }
                return "Could not save photo";
            }
        }
    }
}
