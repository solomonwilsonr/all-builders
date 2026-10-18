package org.safeshelf.android;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.Intent;
import android.content.ActivityNotFoundException;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.BitmapFactory;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.speech.RecognizerIntent;
import android.view.Gravity;
import android.view.View;
import android.webkit.*;
import android.widget.*;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.*;

/** Native Android entry points around the same audited client used by the website. */
public final class MainActivity extends Activity {
    private static final String HOST = "shelf2026-3656b.web.app";
    private static final String CHAT = "https://" + HOST + "/site/chat.html";
    // Shared with web/site/theme.css: blue, mint, ink, soft surfaces and hairlines.
    private static final int BLUE = 0xff0271e4, MINT = 0xffa2f1a9, INK = 0xff001123,
        MUTED = 0xff5d6874, PAPER = 0xffffffff, SOFT = 0xfff5f6f7, LINE = 0xffe4e7eb;
    private Typeface display;
    private static final int FILE = 40, VOICE = 41, CAMERA_PERMISSION = 42;
    private LinearLayout root, navigation;
    private FrameLayout content;
    private WebView web;
    private View home, account;
    private boolean ready;
    private String selected = "Home", pendingAction, pendingText;
    private ValueCallback<Uri[]> fileCallback;
    private boolean capture;
    private final Uri photo = Uri.parse("content://org.safeshelf.android.photos/capture.jpg");

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        display = Typeface.createFromAsset(getAssets(), "web/fonts/SchibstedGrotesk.ttf");
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(PAPER);
        root.setFitsSystemWindows(true);
        content = new FrameLayout(this); root.addView(content, new LinearLayout.LayoutParams(-1, 0, 1));
        navigation = new LinearLayout(this); navigation.setPadding(dp(12), dp(4), dp(12), dp(6)); navigation.setBackgroundColor(Color.WHITE);
        View navigationLine = new View(this); navigationLine.setBackgroundColor(LINE);
        root.addView(navigationLine, new LinearLayout.LayoutParams(-1, dp(1)));
        root.addView(navigation); setContentView(root);
        makeWeb(); makeHome(); makeAccount(); select("Home");
        handleIntent(getIntent());
        if (android.os.Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::handleBack);
        }
    }
    private int dp(float value) { return (int)(getResources().getDisplayMetrics().density * value + .5f); }
    private GradientDrawable shape(int color, int radius) { GradientDrawable d = new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(radius)); return d; }
    private GradientDrawable outlined(int color, int radius) { GradientDrawable d = shape(color,radius); d.setStroke(dp(1),LINE); return d; }
    private LinearLayout column() { LinearLayout l = new LinearLayout(this); l.setOrientation(LinearLayout.VERTICAL); return l; }
    private TextView text(String value, int size, int color, boolean bold) {
        TextView t = new TextView(this); t.setText(value); t.setTextSize(size); t.setTextColor(color);
        t.setTypeface(Typeface.create(display, bold ? Typeface.BOLD : Typeface.NORMAL));
        t.setLineSpacing(dp(2), 1); t.setIncludeFontPadding(false); return t;
    }
    private void gap(LinearLayout parent, int height) { View space = new View(this); parent.addView(space, new LinearLayout.LayoutParams(1, dp(height))); }
    private void divider(LinearLayout parent) { View line = new View(this); line.setBackgroundColor(LINE); parent.addView(line,new LinearLayout.LayoutParams(-1,dp(1))); }
    private Button button(String title, Runnable action, boolean primary) {
        Button b = new Button(this); b.setText(title); b.setAllCaps(false); b.setTextSize(14); b.setTypeface(display);
        b.setTextColor(primary ? Color.WHITE : INK); b.setBackground(primary ? shape(BLUE,2) : outlined(Color.WHITE,2));
        b.setElevation(0); b.setStateListAnimator(null); b.setMinHeight(dp(48));
        b.setPadding(dp(16), dp(12), dp(16), dp(12)); b.setOnClickListener(v -> action.run()); return b;
    }
    private ImageView image(String file) {
        ImageView image = new ImageView(this);
        try (java.io.InputStream in = getAssets().open("web/site/assets/"+file)) { image.setImageBitmap(BitmapFactory.decodeStream(in)); }
        catch(IOException ignored) { image.setVisibility(View.GONE); }
        image.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO); return image;
    }
    private void header(LinearLayout body, String section) {
        LinearLayout bar = new LinearLayout(this); bar.setGravity(Gravity.CENTER_VERTICAL); bar.setPadding(dp(20),dp(16),dp(20),dp(16));
        ImageView logo = new ImageView(this); logo.setImageResource(org.safeshelf.android.R.drawable.ic_shelf);
        bar.addView(logo,new LinearLayout.LayoutParams(dp(27),dp(30)));
        TextView brand = text("SafeShelf",21,INK,false); LinearLayout.LayoutParams brandParams = new LinearLayout.LayoutParams(0,-2,1); brandParams.setMarginStart(dp(9)); bar.addView(brand,brandParams);
        TextView label = text(section,11,MUTED,false); bar.addView(label); body.addView(bar); divider(body);
    }
    private LinearLayout padded(int horizontal, int vertical) { LinearLayout l=column(); l.setPadding(dp(horizontal),dp(vertical),dp(horizontal),dp(vertical)); return l; }
    private void kicker(LinearLayout parent,String label) { TextView t=text(label,12,BLUE,false); t.setLetterSpacing(.04f); parent.addView(t); }
    private View actionTile(String icon, String title, String detail, int tint, Runnable action) {
        LinearLayout tile=padded(15,16); tile.setBackground(outlined(Color.WHITE,2));
        AppIcon glyph=new AppIcon(this,icon,INK); glyph.setBackground(shape(tint,2)); glyph.setPadding(dp(9),dp(9),dp(9),dp(9)); tile.addView(glyph,new LinearLayout.LayoutParams(dp(40),dp(40)));
        gap(tile,14); tile.addView(text(title,16,INK,true)); gap(tile,7); tile.addView(text(detail,12,MUTED,false));
        tile.setOnClickListener(v -> action.run()); tile.setFocusable(true); tile.setContentDescription(title+". "+detail); return tile;
    }
    private void makeHome() {
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true); scroll.setClipToPadding(false);
        LinearLayout body=column(); scroll.addView(body); header(body,"For shoppers");
        LinearLayout intro=padded(22,28); kicker(intro,"Check before you pay"); gap(intro,12);
        TextView title=text("Is it safe?\nIs it real?",40,INK,false); title.setLetterSpacing(-.045f); title.setLineSpacing(0,.99f); intro.addView(title); gap(intro,16);
        intro.addView(text("Shop safer with evidence-backed product checks.",17,INK,false)); gap(intro,10);
        intro.addView(text("Check recalls, buyer hazard reports and suspicious listing signals. See the source behind every answer.",14,MUTED,false)); gap(intro,22);
        intro.addView(button("Check a product   ↗", () -> openChat("focus",null),true),new LinearLayout.LayoutParams(-1,-2)); body.addView(intro);

        FrameLayout scene=new FrameLayout(this); scene.setBackgroundColor(0xffe8f2fd);
        ImageView sky=image("sky.png"); sky.setScaleType(ImageView.ScaleType.CENTER_CROP); scene.addView(sky,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout sceneCopy=padded(18,18); sceneCopy.setBackground(shape(Color.WHITE,2)); sceneCopy.addView(text("Meet Eddy",20,INK,false)); gap(sceneCopy,5);
        sceneCopy.addView(text("Your shopping\ncompanion.",13,MUTED,false));
        FrameLayout.LayoutParams copyParams=new FrameLayout.LayoutParams(dp(166),-2,Gravity.BOTTOM|Gravity.START); copyParams.setMargins(dp(16),0,0,dp(20)); scene.addView(sceneCopy,copyParams);
        ImageView eddy=image("eddy.png"); eddy.setScaleType(ImageView.ScaleType.FIT_CENTER);
        FrameLayout.LayoutParams eddyParams=new FrameLayout.LayoutParams(dp(130),dp(164),Gravity.BOTTOM|Gravity.END); eddyParams.setMargins(0,0,dp(12),0); scene.addView(eddy,eddyParams);
        LinearLayout.LayoutParams sceneParams=new LinearLayout.LayoutParams(-1,dp(196)); sceneParams.setMargins(dp(12),0,dp(12),0); body.addView(scene,sceneParams);

        LinearLayout actions=padded(22,26); kicker(actions,"One check. Clearer choices."); gap(actions,10);
        actions.addView(text("Start with what you have",22,INK,false)); gap(actions,16);
        LinearLayout tiles=new LinearLayout(this);
        LinearLayout.LayoutParams first=new LinearLayout.LayoutParams(0,-1,1); first.setMarginEnd(dp(10));
        tiles.addView(actionTile("scan","Scan a label","Photograph the model number",MINT,()->openChat("scan",null)),first);
        tiles.addView(actionTile("voice","Ask out loud","Review your question before sending",0xffb9c2ff,this::voice),new LinearLayout.LayoutParams(0,-1,1)); actions.addView(tiles);
        gap(actions,12); actions.addView(button("Paste a shopping link   ↗",()->openChat("focus",null),false),new LinearLayout.LayoutParams(-1,-2)); gap(actions,26); divider(actions); gap(actions,22);
        LinearLayout share=new LinearLayout(this); AppIcon shareIcon=new AppIcon(this,"link",BLUE); share.addView(shareIcon,new LinearLayout.LayoutParams(dp(24),dp(24)));
        LinearLayout shareCopy=column(); LinearLayout.LayoutParams shareParams=new LinearLayout.LayoutParams(0,-2,1); shareParams.setMarginStart(dp(12)); share.addView(shareCopy,shareParams);
        shareCopy.addView(text("Already found something?",16,INK,false)); gap(shareCopy,6); shareCopy.addView(text("Share a product from your shopping app to SafeShelf. Review it here, then press Send.",13,MUTED,false)); actions.addView(share); gap(actions,24);
        LinearLayout note=padded(14,14); note.setBackgroundColor(SOFT); note.addView(text("Private and honest, by default.",14,INK,false)); gap(note,6);
        note.addView(text("Nothing is submitted until you request a check. No matching recall does not guarantee safety.",12,MUTED,false)); actions.addView(note); body.addView(actions);
        home=scroll; content.addView(home);
    }
    private void infoSection(LinearLayout body,String icon,String title,String description,int tint) {
        LinearLayout row=new LinearLayout(this); row.setPadding(0,dp(20),0,dp(20));
        AppIcon glyph=new AppIcon(this,icon,INK); glyph.setBackground(shape(tint,2)); glyph.setPadding(dp(9),dp(9),dp(9),dp(9)); row.addView(glyph,new LinearLayout.LayoutParams(dp(40),dp(40)));
        LinearLayout copy=column(); LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(0,-2,1); params.setMarginStart(dp(14)); row.addView(copy,params);
        copy.addView(text(title,16,INK,false)); gap(copy,7); copy.addView(text(description,13,MUTED,false)); body.addView(row); divider(body);
    }
    private void makeAccount() {
        ScrollView scroll=new ScrollView(this); LinearLayout body=column(); scroll.addView(body); header(body,"Your account");
        LinearLayout intro=padded(22,28); kicker(intro,"Your SafeShelf"); gap(intro,12);
        TextView heading=text("A little more\npeace of mind.",34,INK,false); heading.setLetterSpacing(-.04f); intro.addView(heading); gap(intro,14);
        intro.addView(text("Manage your account and keep the products you care about close.",14,MUTED,false)); gap(intro,22);
        intro.addView(button("Sign in / manage account   ↗",()->openChat("account",null),true),new LinearLayout.LayoutParams(-1,-2)); body.addView(intro);
        LinearLayout details=padded(22,0);
        infoSection(details,"Account","Choose how to sign in","Use email and password, create an account, or try a guest check. One guest check, or five checks a day with an account.",0xffe8f2fd);
        infoSection(details,"My Shelf","Products worth watching","Tap Watch for recalls under an answer. Your watched products stay linked to this app’s data; extension saves are separate.",MINT);
        infoSection(details,"shield","Recall updates","Open My Shelf for the latest status returned by the service. Background push alerts are not connected yet.",0xffb9c2ff);
        infoSection(details,"scan","Your privacy, your choice","Links and photos are sent when you request a check. Camera access is optional. Clearing app data removes access to this device’s watchlist.",0xffffe04a);
        gap(details,22); details.addView(button("Visit the SafeShelf website   ↗",()->external(Uri.parse("https://"+HOST+"/site/")),false),new LinearLayout.LayoutParams(-1,-2)); gap(details,16);
        details.addView(text("Google sign-in is available on the website. The app supports email and guest sign-in.",12,MUTED,false)); gap(details,24);
        TextView version=text("SafeShelf for Android · 0.2.0",11,MUTED,false); version.setGravity(Gravity.CENTER); details.addView(version); gap(details,24); body.addView(details);
        account=scroll; content.addView(account);
    }
    private void select(String tab) {
        selected=tab; home.setVisibility(tab.equals("Home") ? View.VISIBLE : View.GONE); account.setVisibility(tab.equals("Account") ? View.VISIBLE : View.GONE);
        web.setVisibility(tab.equals("Eddy") || tab.equals("My Shelf") ? View.VISIBLE : View.GONE); navigation.removeAllViews();
        for(String label:new String[]{"Home","Eddy","My Shelf","Account"}) {
            boolean active=label.equals(tab); LinearLayout item=column(); item.setGravity(Gravity.CENTER); item.setPadding(0,dp(8),0,dp(5));
            AppIcon icon=new AppIcon(this,label,active ? BLUE : MUTED); item.addView(icon,new LinearLayout.LayoutParams(dp(22),dp(22))); gap(item,5);
            item.addView(text(label,10,active ? BLUE : MUTED,active)); item.setSelected(active); item.setFocusable(true); item.setContentDescription(label+(active ? ", selected" : ""));
            item.setOnClickListener(v->{if(label.equals("Eddy"))openChat("closeShelf",null);else if(label.equals("My Shelf")){openChat("shelf",null);select("My Shelf");}else select(label);});
            navigation.addView(item,new LinearLayout.LayoutParams(0,dp(60),1));
        }
    }
    private boolean trusted(Uri uri) { return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && (uri.getPort() == -1 || uri.getPort() == 443); }
    private void makeWeb() {
        web = new WebView(this); web.setBackgroundColor(Color.WHITE);
        // This client is text and still images; software composition avoids stale drawer tiles
        // on devices whose WebView GPU driver does not invalidate overlapping layers correctly.
        web.setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        WebSettings s = web.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setAllowFileAccess(false); s.setAllowContentAccess(true); s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(true);
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                if (!trusted(req.getUrl())) return null;
                String path = req.getUrl().getPath();
                if (path == null || path.contains("..") || !req.getMethod().equals("GET")) return blocked();
                try {
                    String mime = path.endsWith(".html") ? "text/html" : path.endsWith(".js") ? "text/javascript" : path.endsWith(".ttf") ? "font/ttf" : path.endsWith(".css") ? "text/css" : path.endsWith(".png") ? "image/png" : path.endsWith(".svg") ? "image/svg+xml" : "image/jpeg";
                    return new WebResourceResponse(mime, "UTF-8", getAssets().open("web" + path));
                } catch (IOException e) { return blocked(); }
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri uri = req.getUrl();
                if (trusted(uri) && "/site/chat.html".equals(uri.getPath())) return false;
                if (req.isForMainFrame()) external(uri);
                return true;
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (!trusted(Uri.parse(url))) return;
                ready = true; applyPending();
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError error) {
                if (req.isForMainFrame()) { ready = false; new AlertDialog.Builder(MainActivity.this).setTitle("Couldn't open Eddy").setMessage("Try opening the chat again. Live checks also need an internet connection.").setPositiveButton("Retry", (d,w) -> web.loadUrl(CHAT)).setNegativeButton("Home", (d,w) -> select("Home")).show(); }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                if (params.isCaptureEnabled()) {
                    capture = true;
                    if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
                    else launchCamera();
                } else { capture = false; pickPhoto(); }
                return true;
            }
            @Override public void onPermissionRequest(PermissionRequest request) { request.deny(); }
        });
        content.addView(web, new FrameLayout.LayoutParams(-1, -1)); web.loadUrl(CHAT);
    }
    private WebResourceResponse blocked() { return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", Collections.emptyMap(), new ByteArrayInputStream("Not bundled".getBytes())); }
    private void openChat(String action, String value) { pendingAction = action; pendingText = value; select("Eddy"); applyPending(); }
    private void applyPending() {
        if (!ready || !trusted(Uri.parse(web.getUrl() == null ? "" : web.getUrl()))) return;
        String action = pendingAction, value = pendingText; pendingAction = null; pendingText = null;
        String js = "(()=>{window.__ssWait=0;const run=()=>{if(typeof window.safeshelfSignIn!=='function'){if(++window.__ssWait<100)setTimeout(run,100);return;}";
        if (value != null) js += "const q=document.getElementById('q');q.value=" + JSONObject.quote(value) + ";q.dispatchEvent(new Event('input'));q.focus();";
        if ("focus".equals(action)) js += "document.getElementById('q').focus();";
        if ("scan".equals(action)) js += "document.getElementById('scan').click();";
        if ("shelf".equals(action)) js += "document.getElementById('shelfBtn').click();";
        if ("closeShelf".equals(action)) js += "document.getElementById('shelfClose').click();";
        if ("account".equals(action)) js += "const a=document.querySelector('.acct-face');if(a)a.click();else window.safeshelfSignIn?.();";
        js += "};run();})()";
        if (action != null || value != null) web.evaluateJavascript(js, null);
    }
    private void pickPhoto() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
        try { startActivityForResult(Intent.createChooser(intent, "Choose a product photo"), FILE); }
        catch (ActivityNotFoundException e) { finishFile(null); Toast.makeText(this, "No photo picker is installed", Toast.LENGTH_LONG).show(); }
    }
    private void launchCamera() {
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT, photo);
        intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION); intent.setClipData(ClipData.newRawUri("Product label", photo));
        try { startActivityForResult(intent, FILE); }
        catch (ActivityNotFoundException e) { capture = false; pickPhoto(); }
    }
    private void finishFile(Uri[] result) { if (fileCallback != null) { fileCallback.onReceiveValue(result); fileCallback = null; } }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == CAMERA_PERMISSION) { if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) launchCamera(); else { capture = false; pickPhoto(); } }
    }
    private void voice() {
        Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_PROMPT, "Ask about a product");
        try { startActivityForResult(i, VOICE); }
        catch (ActivityNotFoundException e) { Toast.makeText(this, "Voice input isn't installed. You can type your question.", Toast.LENGTH_LONG).show(); openChat("focus", null); }
    }
    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE) finishFile(resultCode != RESULT_OK ? null : capture ? new Uri[]{photo} : WebChromeClient.FileChooserParams.parseResult(resultCode, data));
        if (requestCode == VOICE && resultCode == RESULT_OK && data != null) {
            ArrayList<String> words = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (words != null && !words.isEmpty()) openChat(null, words.get(0));
        }
    }
    private void external(Uri uri) {
        if (!Arrays.asList("https", "http", "mailto", "tel").contains(uri.getScheme())) return;
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
        catch (ActivityNotFoundException e) { Toast.makeText(this, "No app can open this link", Toast.LENGTH_SHORT).show(); }
    }
    private void handleIntent(Intent intent) {
        if (Intent.ACTION_SEND.equals(intent.getAction()) && "text/plain".equals(intent.getType())) {
            String value = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (value != null) openChat(null, value.length() > 16000 ? value.substring(0,16000) : value);
        }
    }
    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); setIntent(intent); handleIntent(intent); }
    // Android 13+ uses the dispatcher registered in onCreate; retain this for Android 8–12.
    @android.annotation.SuppressLint("GestureBackNavigation")
    @Override public void onBackPressed() { handleBack(); }
    private void handleBack() {
        if (!selected.equals("Home")) { if (ready) web.evaluateJavascript("document.getElementById('shelfClose')?.click()", null); select("Home"); }
        else finish();
    }
    @Override protected void onDestroy() { finishFile(null); web.destroy(); super.onDestroy(); }
}
