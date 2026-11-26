package my.utmkl.realworld;

import android.os.Bundle;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.WebView;
import android.widget.Toast;

import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.WebViewListener;

public class MainActivity extends BridgeActivity {
    private static long lastRendererRestart;

    @Override
    protected void onCreate(Bundle state) {
        registerPlugin(SceneBridge.class);
        bridgeBuilder.addWebViewListener(new WebViewListener() {
            @Override
            public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
                long now = android.os.SystemClock.elapsedRealtime();
                if (lastRendererRestart != 0 && now - lastRendererRestart < 30000) {
                    Toast.makeText(MainActivity.this, "WebView 渲染失败，请更新系统 WebView 后重试。", Toast.LENGTH_LONG).show();
                    finish();
                    return true;
                }
                lastRendererRestart = now;
                getPreferences(MODE_PRIVATE).edit().putBoolean("safeNextLoad", true).apply();
                runOnUiThread(MainActivity.this::recreate);
                return true;
            }
        });
        super.onCreate(state);
        immersive();
    }

    @Override
    public void onWindowFocusChanged(boolean focused) {
        super.onWindowFocusChanged(focused);
        if (focused) immersive();
    }

    private void immersive() {
        WindowInsetsControllerCompat controls = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        controls.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
        controls.hide(WindowInsetsCompat.Type.systemBars());
    }
}
