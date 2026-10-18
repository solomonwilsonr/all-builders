# SafeShelf for Android

Version 0.4.0 adapts the supplied AI workspace design reference with rounded white cards, soft blue backgrounds, pill controls, a compact greeting, and a dark floating navigation dock. SafeShelf's blue #0271E4, mint #A2F1A9, ink #001123, Schibsted Grotesk typeface and Eddy/pixel artwork remain. The styling covers native Home/Account/navigation plus chat, results, My Shelf, and sign-in. The reference images are not packaged as app assets.


Installable first version for shoppers and families. Native Java home, navigation, voice entry and Android Share integration surround the existing SafeShelf chat, packaged inside the APK. Product checks, evidence, alternatives, label-image analysis and after-purchase drafts use the existing live API. This is a hybrid Android app, not a rewrite of the investigation engine.

## Run

Open this directory in Android Studio and let Gradle sync. Requirements: JDK 17 or 21, Android SDK platform 36, and an Android 8.0+ device with an up-to-date Android System WebView.

```sh
export ANDROID_HOME="$HOME/Library/Android/sdk"
./gradlew assembleDebug lintDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

The debug APK is `app/build/outputs/apk/debug/app-debug.apk`. It is signed for local installation, not Play Store distribution. Use your own release signing configuration for publication; no signing credentials are included.

## Included

- Native Home, Eddy, My Shelf and Account navigation.
- Share a product link from another app into Eddy. Shared text is prefilled for review, never submitted automatically.
- Existing streamed investigations, sourced results, follow-up chat, language selection, alternatives and after-purchase drafts.
- Label photo capture through the camera app, with a system photo-picker fallback if camera permission is declined or no camera app is installed.
- Screenshot/photo attachments through the system picker; no storage permission required.
- Native voice dictation from Home on devices with a speech-recognition activity. The user reviews recognized text before submitting.
- Existing email/password, account registration, password reset and guest sign-in. Session storage remains in this app's WebView.
- Existing API watchlist drawer, using the signed-in account or a device-local guest owner reference. This is distinct from the extension's Firestore shelf.

## Current limits

- No background push notifications. My Shelf displays status returned by the server; the app does not schedule recall re-checks.
- Google OAuth is hidden in the embedded client because it needs a native authentication integration. Google sign-in on the external website does not sign in the app. Email/guest availability depends on the existing Firebase project configuration.
- The web client's camera livestream and browser speech recognition are not supported here. Use label photo capture and Home's native voice action instead. Read-aloud availability depends on WebView speech support.
- Unsent text drafts survive a page reload within the same WebView session. Chat history remains in memory during navigation; it is not restored after the OS kills the app. Authentication and the watchlist owner reference persist until app data is cleared.
- Live checking needs internet and the existing production API. A missing recall is not proof of safety.
- No Play Store upload, native Firebase Google sign-in or barcode lookup is included.

## Implementation

`bundleWeb` copies an explicit allowlist from `../web` into generated Android assets. It links the Android theme and reference-adaptation stylesheets and hides Google OAuth in the Android copy only. It does not alter the website sources or include `.env`, deployment logs or server credentials.

The WebView intercepts the existing Firebase Hosting origin and serves bundled files over that HTTPS origin, preserving Firebase authorized-domain behavior. Unknown paths on that origin receive a 404. Firebase SDK modules/fonts and the API are fetched over HTTPS. External navigation opens in the user's browser. There is no native JavaScript bridge, mixed-content allowance, TLS bypass, or unrestricted file access.

`MainActivity.java` owns native navigation, shared-text intake, dictation, runtime camera permission and file upload callbacks. `PhotoProvider.java` exposes only a single cache photo through temporary URI grants. Android 13+ back navigation uses the platform back dispatcher; older versions use the legacy callback.

## Validation

Build and lint: `./gradlew assembleDebug lintDebug`. Emulator smoke testing covers native navigation, bundled chat rendering, shared-link prefill, sign-in UI and the shelf drawer. Live AI checks require service quota and are not mocked by the app. Physical-device camera, vendor speech support and full authenticated purchase investigations should be checked before release.

To repeat the client smoke checks against a debug install:

```sh
ADB="$ANDROID_HOME/platform-tools/adb" node scripts/smoke.mjs
```

This uses Node 22+ and the debug WebView's local DevTools socket. It verifies shared-link prefill, no automatic submission, Firebase client initialization, email sign-in UI, the Google OAuth restriction, and watchlist drawer opening/closing. It does not create an account or consume a product-check quota.

Version 0.2.0 verification: debug build and lint passed, as did the client smoke checks including theme color, square input controls, bundled font, sharing, sign-in UI and watchlist controls. After recovering from local Android System UI instability, Home, Eddy, Account and My Shelf were reviewed in the emulator. Physical-device camera and full live investigations still need release validation.

Version 0.3.0 usability: Home shortcuts appear above the artwork; the main tab is labeled Check. Shopper checks default to no demo product, samples are explicitly labeled, and developer controls are hidden. Text drafts are kept in session storage. New check requires confirmation before clearing a draft/conversation; busy requests cannot be cleared. Back closes confirmation, sign-in and shelf panels before leaving the check. My Shelf has actionable empty-state guidance and correctly describes the lack of push alerts. Account shows current sign-in status when available. The attachment picker accepts the photo/PDF types supported by the bundled website.

Validation: debug build and lint plus emulator smoke checks for sharing, auth UI, theme, shelf layout, real-product defaults, draft protection, modal Back handling and busy guards. Live AI checks and physical-device camera behavior remain outside these smoke checks.

Native navigation checks can be repeated with `ADB="$ANDROID_HOME/platform-tools/adb" python3 scripts/navigation.py`. These verify that both the shelf Close button and Android Back return to Check, and the next Back returns Home. They use the actual Android view hierarchy and do not submit AI checks.

Version 0.4.0 keeps the existing product-check and account behavior while adding a functional Home question field that opens the question in Check for review. Quick actions open label capture, dictation, My Shelf and chat. Rounded cards, profile controls and the dock use the same SafeShelf palette as the embedded client. Existing draft protection, safe new-check confirmation, real-product defaults, busy guards and navigation behavior remain.

Version 0.4.0 validation: debug build and lint passed. Emulator checks passed for sharing, Firebase UI, theme, sample isolation, drafts, new-check confirmation, busy guards, shelf layout, reachable sign-in controls, panel navigation and the Home question handoff. Home, Check, My Shelf, Account and sign-in were visually reviewed at a typical phone width. Screenshots are in `screenshots/`. Live AI investigations and physical-device camera behavior were not exercised by these checks.
