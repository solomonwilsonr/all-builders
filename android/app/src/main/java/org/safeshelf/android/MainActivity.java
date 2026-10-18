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
        MUTED = 0xff5d6874, PAPER = 0xfff3f7fb, SOFT = 0xffedf4fa, LINE = 0xffe1eaf2;
    private Typeface display;
    private static final int FILE = 40, VOICE = 41, CAMERA_PERMISSION = 42;
    private LinearLayout root, navigation;
    private FrameLayout content;
    private WebView web;
    private View home, account;
    private TextView accountSummary;
    private Button accountButton;
    private boolean ready;
    private String selected = "Home", pendingAction, pendingText;
    private ValueCallback<Uri[]> fileCallback;
    private boolean capture;
    private String[] uploadTypes = {"image/*"};
    private int actionGeneration;
    private final Uri photo = Uri.parse("content://org.safeshelf.android.photos/capture.jpg");

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        display = Typeface.createFromAsset(getAssets(), "web/fonts/SchibstedGrotesk.ttf");
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(PAPER);
        root.setFitsSystemWindows(true); root.setFocusableInTouchMode(true);
        content = new FrameLayout(this); root.addView(content, new LinearLayout.LayoutParams(-1, 0, 1));
        navigation = new LinearLayout(this); navigation.setPadding(dp(6),dp(6),dp(6),dp(6)); navigation.setBackground(shape(INK,36));
        LinearLayout.LayoutParams dockParams=new LinearLayout.LayoutParams(-1,-2);
        dockParams.setMargins(dp(16),dp(8),dp(16),dp(10)); root.addView(navigation,dockParams); setContentView(root);
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
        b.setTextColor(primary ? Color.WHITE : INK); b.setBackground(primary ? shape(BLUE,26) : shape(SOFT,26));
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
        LinearLayout bar=new LinearLayout(this); bar.setGravity(Gravity.CENTER_VERTICAL); bar.setPadding(dp(22),dp(20),dp(22),dp(18));
        ImageView logo=new ImageView(this);logo.setImageResource(org.safeshelf.android.R.drawable.ic_shelf);
        logo.setBackground(shape(Color.WHITE,24));logo.setPadding(dp(10),dp(10),dp(10),dp(10));
        bar.addView(logo,new LinearLayout.LayoutParams(dp(48),dp(48)));
        LinearLayout copy=column();LinearLayout.LayoutParams copyParams=new LinearLayout.LayoutParams(0,-2,1);copyParams.setMarginStart(dp(12));bar.addView(copy,copyParams);
        copy.addView(text(section,17,INK,true));gap(copy,4);copy.addView(text("SafeShelf · Your shopping companion",11,MUTED,false));
        AppIcon profile=new AppIcon(this,"Account",BLUE);profile.setPadding(dp(12),dp(12),dp(12),dp(12));profile.setBackground(shape(Color.WHITE,24));
        profile.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);profile.setContentDescription("Open your account");profile.setFocusable(true);profile.setOnClickListener(v->select("Account"));
        bar.addView(profile,new LinearLayout.LayoutParams(dp(48),dp(48)));body.addView(bar);
    }
    private LinearLayout padded(int horizontal, int vertical) { LinearLayout l=column(); l.setPadding(dp(horizontal),dp(vertical),dp(horizontal),dp(vertical)); return l; }
    private void kicker(LinearLayout parent,String label) { TextView t=text(label,12,BLUE,false); t.setLetterSpacing(.04f); parent.addView(t); }
    private View actionTile(String icon, String title, String detail, int tint, Runnable action) {
        LinearLayout tile=padded(17,18);tile.setBackground(shape(Color.WHITE,24));tile.setMinimumHeight(dp(148));
        LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);
        AppIcon glyph=new AppIcon(this,icon,INK);glyph.setBackground(shape(tint,22));glyph.setPadding(dp(11),dp(11),dp(11),dp(11));top.addView(glyph,new LinearLayout.LayoutParams(dp(44),dp(44)));
        View spacer=new View(this);top.addView(spacer,new LinearLayout.LayoutParams(0,1,1));AppIcon arrow=new AppIcon(this,"arrow",MUTED);top.addView(arrow,new LinearLayout.LayoutParams(dp(18),dp(18)));tile.addView(top);
        gap(tile,18);tile.addView(text(title,17,INK,true));gap(tile,7);tile.addView(text(detail,12,MUTED,false));
        tile.setOnClickListener(v->action.run());tile.setFocusable(true);tile.setContentDescription(title+". "+detail);return tile;
    }
    private void tileRow(LinearLayout body,View left,View right) {
        LinearLayout row=new LinearLayout(this);LinearLayout.LayoutParams first=new LinearLayout.LayoutParams(0,-1,1);first.setMarginEnd(dp(12));
        row.addView(left,first);row.addView(right,new LinearLayout.LayoutParams(0,-1,1));body.addView(row);
    }
    private void makeHome() {
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setClipToPadding(false);scroll.setVerticalScrollBarEnabled(false);
        LinearLayout body=column();scroll.addView(body);
        GradientDrawable wash=new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0xffd6eaff,0xffedf5fc,PAPER});body.setBackground(wash);
        header(body,"Hello, shopper");
        LinearLayout main=padded(20,4);
        LinearLayout hero=padded(20,21);hero.setBackground(shape(Color.WHITE,28));
        LinearLayout heroTop=new LinearLayout(this);heroTop.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout heroCopy=column();LinearLayout.LayoutParams heroCopyParams=new LinearLayout.LayoutParams(0,-2,1);heroTop.addView(heroCopy,heroCopyParams);
        kicker(heroCopy,"Your shopping, simplified");gap(heroCopy,11);
        TextView title=text("Shop safer.\nWith Eddy.",27,INK,true);title.setLetterSpacing(-.04f);heroCopy.addView(title);
        ImageView eddy=image("eddy.png");eddy.setScaleType(ImageView.ScaleType.FIT_CENTER);heroTop.addView(eddy,new LinearLayout.LayoutParams(dp(78),dp(96)));hero.addView(heroTop);
        gap(hero,14);hero.addView(text("Ask Eddy about a product before you buy. Get a clear answer with the evidence behind it.",13,MUTED,false));gap(hero,18);
        LinearLayout entry=new LinearLayout(this);entry.setGravity(Gravity.CENTER_VERTICAL);entry.setPadding(dp(15),dp(5),dp(5),dp(5));entry.setBackground(shape(SOFT,28));
        EditText question=new EditText(this);question.setHint("Paste a link or ask Eddy…");question.setTextSize(14);question.setTypeface(display);question.setTextColor(INK);question.setHintTextColor(MUTED);
        question.setBackgroundColor(Color.TRANSPARENT);question.setPadding(0,dp(8),dp(6),dp(8));question.setMaxLines(2);question.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        question.setContentDescription("Product link or question");entry.addView(question,new LinearLayout.LayoutParams(0,-2,1));
        AppIcon send=new AppIcon(this,"arrow",Color.WHITE);send.setPadding(dp(14),dp(14),dp(14),dp(14));send.setBackground(shape(BLUE,24));send.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);send.setContentDescription("Open product check");send.setFocusable(true);
        send.setOnClickListener(v->{String value=question.getText().toString().trim();openChat(value.isEmpty()?"focus":null,value.isEmpty()?null:value);});entry.addView(send,new LinearLayout.LayoutParams(dp(48),dp(48)));hero.addView(entry);
        gap(hero,9);hero.addView(text("Review your question before sending it for a check.",11,MUTED,false));main.addView(hero);gap(main,25);
        main.addView(text("How can we help?",20,INK,true));gap(main,13);
        tileRow(main,actionTile("scan","Scan a label","Use a photo of the model number",MINT,()->openChat("scan",null)),actionTile("voice","Ask out loud","Speak, review, then send",0xffe6eaff,this::voice));gap(main,12);
        tileRow(main,actionTile("My Shelf","My Shelf","See products you’re watching",0xffe8f2fd,()->{openChat("shelf",null);select("My Shelf");}),actionTile("Eddy","Chat with Eddy","Ask about safety or authenticity",0xffe4f7e6,()->openChat("focus",null)));gap(main,25);
        main.addView(text("Keep good choices close",20,INK,true));gap(main,13);
        LinearLayout saved=padded(20,20);saved.setBackground(shape(Color.WHITE,24));
        LinearLayout savedTop=new LinearLayout(this);savedTop.setGravity(Gravity.CENTER_VERTICAL);AppIcon shield=new AppIcon(this,"shield",BLUE);savedTop.addView(shield,new LinearLayout.LayoutParams(dp(24),dp(24)));
        TextView savedTitle=text("Watch it after you buy",17,INK,true);LinearLayout.LayoutParams savedTitleParams=new LinearLayout.LayoutParams(0,-2,1);savedTitleParams.setMarginStart(dp(10));savedTop.addView(savedTitle,savedTitleParams);saved.addView(savedTop);gap(saved,11);
        saved.addView(text("Choose “Watch for recalls” beneath a check. Your saved products and the latest status appear in My Shelf.",13,MUTED,false));gap(saved,16);
        saved.addView(button("Open My Shelf   ↗",()->{openChat("shelf",null);select("My Shelf");},false),new LinearLayout.LayoutParams(-1,-2));main.addView(saved);gap(main,19);
        TextView privacy=text("Evidence first. No matching recall does not guarantee safety. Share a shopping link to SafeShelf whenever you need a second look.",11,MUTED,false);main.addView(privacy);gap(main,18);body.addView(main);
        home=scroll;content.addView(home);
    }
    private void infoSection(LinearLayout body,String icon,String title,String description,int tint) {
        LinearLayout row=new LinearLayout(this);row.setPadding(dp(17),dp(18),dp(17),dp(18));row.setBackground(shape(Color.WHITE,24));
        AppIcon glyph=new AppIcon(this,icon,INK);glyph.setBackground(shape(tint,22));glyph.setPadding(dp(11),dp(11),dp(11),dp(11));row.addView(glyph,new LinearLayout.LayoutParams(dp(44),dp(44)));
        LinearLayout copy=column();LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(0,-2,1);params.setMarginStart(dp(13));row.addView(copy,params);
        copy.addView(text(title,16,INK,true));gap(copy,7);copy.addView(text(description,12,MUTED,false));body.addView(row);gap(body,12);
    }
    private void makeAccount() {
        ScrollView scroll=new ScrollView(this);scroll.setVerticalScrollBarEnabled(false);LinearLayout body=column();body.setBackgroundColor(PAPER);scroll.addView(body);header(body,"Your account");
        LinearLayout main=padded(20,4);LinearLayout profile=padded(22,22);profile.setBackground(shape(Color.WHITE,28));
        AppIcon avatar=new AppIcon(this,"Account",BLUE);avatar.setPadding(dp(15),dp(15),dp(15),dp(15));avatar.setBackground(shape(0xffe8f2fd,30));profile.addView(avatar,new LinearLayout.LayoutParams(dp(60),dp(60)));gap(profile,16);
        profile.addView(text("Your SafeShelf",27,INK,true));gap(profile,10);accountSummary=text("Sign in to check products and keep track of what you’re watching.",14,MUTED,false);profile.addView(accountSummary);gap(profile,20);
        accountButton=button("Sign in or create an account   ↗",()->openChat("account",null),true);profile.addView(accountButton,new LinearLayout.LayoutParams(-1,-2));main.addView(profile);gap(main,24);
        main.addView(text("Made for your peace of mind",19,INK,true));gap(main,13);
        infoSection(main,"Account","Your account & checks","Email or guest sign-in. One guest check, or five daily checks with an account.",0xffe8f2fd);
        infoSection(main,"My Shelf","Products you’re watching","Save products with “Watch for recalls”. Signed-in shelves follow your account; guest shelves stay on this device.",MINT);
        infoSection(main,"shield","Recall updates","Open My Shelf to see the latest status. Background phone notifications are not connected yet.",0xffe6eaff);
        infoSection(main,"scan","Privacy, on your terms","A link or photo is sent when you request a check. Camera access is optional. Clearing app data removes a guest shelf.",0xfffff2dc);
        gap(main,6);main.addView(button("Visit the SafeShelf website   ↗",()->external(Uri.parse("https://"+HOST+"/site/")),false),new LinearLayout.LayoutParams(-1,-2));gap(main,14);
        main.addView(text("Google sign-in is available on the website. Use email or guest access in this app.",11,MUTED,false));gap(main,22);
        TextView version=text("SafeShelf for Android · 0.4.0",11,MUTED,false);version.setGravity(Gravity.CENTER);main.addView(version);gap(main,14);body.addView(main);
        account=scroll;content.addView(account);
    }
    private void select(String tab) {
        selected=tab;
        if(!tab.equals("Eddy")) {
            android.view.inputmethod.InputMethodManager keyboard=(android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE);
            keyboard.hideSoftInputFromWindow(root.getWindowToken(),0);root.requestFocus();
        }
        if(tab.equals("Account")) updateAccount();
        home.setVisibility(tab.equals("Home") ? View.VISIBLE : View.GONE); account.setVisibility(tab.equals("Account") ? View.VISIBLE : View.GONE);
        web.setVisibility(tab.equals("Eddy") || tab.equals("My Shelf") ? View.VISIBLE : View.GONE); navigation.removeAllViews();
        for(String label:new String[]{"Home","Eddy","My Shelf","Account"}) {
            boolean active=label.equals(tab); LinearLayout item=column(); item.setGravity(Gravity.CENTER); item.setPadding(0,dp(7),0,dp(6));
            if(active)item.setBackground(shape(0xffe8f2fd,28));
            AppIcon icon=new AppIcon(this,label,active ? BLUE : 0xffc7d4df); item.addView(icon,new LinearLayout.LayoutParams(dp(22),dp(22))); gap(item,5);
            String displayLabel=label.equals("Eddy") ? "Check" : label;
            TextView tabLabel=text(displayLabel,11,active ? 0xff0a5fc0 : 0xffc7d4df,active);
            tabLabel.setGravity(Gravity.CENTER);
            tabLabel.setTextAlignment(View.TEXT_ALIGNMENT_CENTER);
            tabLabel.setSingleLine(true);
            tabLabel.setEllipsize(android.text.TextUtils.TruncateAt.END);
            item.addView(tabLabel,new LinearLayout.LayoutParams(-1,-2)); item.setSelected(active); item.setFocusable(true); item.setContentDescription(displayLabel+(active ? ", selected" : ""));
            item.setOnClickListener(v->{if(label.equals("Eddy"))openChat("closeShelf",null);else if(label.equals("My Shelf")){openChat("shelf",null);select("My Shelf");}else select(label);});
            LinearLayout.LayoutParams tabParams=new LinearLayout.LayoutParams(0,dp(60),1);tabParams.setMargins(dp(2),0,dp(2),0);navigation.addView(item,tabParams);
        }
    }
    private void updateAccount() {
        if (!ready) return;
        web.evaluateJavascript("window.safeshelfAccount ? JSON.stringify({guest:window.safeshelfAccount.guest,name:window.safeshelfAccount.name || window.safeshelfAccount.email || 'Your account',checks:window.safeshelfAccount.text()}) : null", result -> {
            try {
                Object value=new org.json.JSONTokener(result).nextValue();
                if (!(value instanceof String)) {
                    accountSummary.setText("Sign in to check products and keep track of what you’re watching.");
                    accountButton.setText("Sign in or create an account   ↗"); return;
                }
                JSONObject info=new JSONObject((String)value);
                accountSummary.setText((info.optBoolean("guest") ? "You’re using guest access." : "Signed in as "+info.optString("name")+".")+"\n"+info.optString("checks"));
                accountButton.setText(info.optBoolean("guest") ? "Sign in for more checks   ↗" : "Manage account   ↗");
            } catch (org.json.JSONException ignored) { /* Keep the signed-out guidance until account data is ready. */ }
        });
    }
    private boolean trusted(Uri uri) { return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && (uri.getPort() == -1 || uri.getPort() == 443); }
    private void makeWeb() {
        web = new WebView(this); web.setBackgroundColor(PAPER);
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
                if (req.isForMainFrame() && "safeshelf".equals(uri.getScheme()) && trusted(Uri.parse(view.getUrl() == null ? "" : view.getUrl()))) {
                    if ("check".equals(uri.getHost())) { select("Eddy"); return true; }
                    if ("home".equals(uri.getHost())) { select("Home"); return true; }
                }
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
                uploadTypes = Arrays.stream(params.getAcceptTypes()).flatMap(t -> Arrays.stream(t.split(","))).map(String::trim).filter(t -> t.startsWith("image/") || t.equals("application/pdf")).toArray(String[]::new);
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
        int generation=++actionGeneration;
        String waitFor = "account".equals(action) ? "typeof window.safeshelfSignIn!=='function'" : "!document.getElementById('q')";
        String js = "(()=>{window.__ssWait=0;window.__ssAction="+generation+";const run=()=>{if(window.__ssAction!=="+generation+")return;if("+waitFor+"){if(++window.__ssWait<100)setTimeout(run,100);return;}";
        if (value != null) js += "document.getElementById('shelfClose').click();const q=document.getElementById('q');q.value=" + JSONObject.quote(value) + ";q.dispatchEvent(new Event('input'));q.focus();window.androidUx?.announce('Ready to review. Press Send when you are ready.');";
        if ("focus".equals(action)) js += "document.getElementById('shelfClose').click();document.getElementById('q').focus();";
        if ("scan".equals(action)) js += "document.getElementById('scan').click();";
        if ("shelf".equals(action)) js += "document.getElementById('shelfBtn').click();";
        if ("closeShelf".equals(action)) js += "document.getElementById('shelfClose').click();";
        if ("account".equals(action)) js += "const a=document.querySelector('.acct-face');if(a)a.click();else window.safeshelfSignIn?.();";
        js += "};run();})()";
        if (action != null || value != null) web.evaluateJavascript(js, null);
    }
    private void pickPhoto() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT).addCategory(Intent.CATEGORY_OPENABLE);
        if (capture || uploadTypes.length == 0) intent.setType("image/*");
        else if (uploadTypes.length == 1) intent.setType(uploadTypes[0]);
        else intent.setType("*/*").putExtra(Intent.EXTRA_MIME_TYPES, uploadTypes);
        try { startActivityForResult(Intent.createChooser(intent, "Choose a photo or manual"), FILE); }
        catch (ActivityNotFoundException e) { finishFile(null); Toast.makeText(this, "No photo picker is installed", Toast.LENGTH_LONG).show(); }
    }
    private void launchCamera() {
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT, photo);
        intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION); intent.setClipData(ClipData.newRawUri("Product label", photo));
        try { startActivityForResult(intent, FILE); }
        catch (ActivityNotFoundException e) { capture = false; uploadTypes = new String[]{"image/*"}; pickPhoto(); }
    }
    private void finishFile(Uri[] result) { if (fileCallback != null) { fileCallback.onReceiveValue(result); fileCallback = null; } }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == CAMERA_PERMISSION) { if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) launchCamera(); else { capture = false; uploadTypes = new String[]{"image/*"}; pickPhoto(); } }
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
        if ((selected.equals("Eddy") || selected.equals("My Shelf")) && ready) {
            web.evaluateJavascript("window.androidUx?.back() || 'home'", result -> {
                if ("\"shelf\"".equals(result)) select("Eddy");
                else if ("\"home\"".equals(result)) select("Home");
            });
        } else if (!selected.equals("Home")) select("Home");
        else finish();
    }
    @Override protected void onDestroy() { finishFile(null); web.destroy(); super.onDestroy(); }
}
