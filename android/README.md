# SafeShelf for Android

Version 0.2.0 matches the blue/mint SafeShelf website (`web/site/theme.css`): Schibsted Grotesk typography, blue #0271E4, mint #A2F1A9, ink #001123, square controls, fine borders and the original pixel sky/Eddy artwork. The same theme covers native Home/Account/navigation and the embedded chat, results, watchlist and sign-in surfaces. The font is bundled with its OFL license for use without a font download.


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
- Existing API watchlist drawer, using its device-local owner reference. This is distinct from the extension's Firestore shelf.

## Current limits

- No background push notifications. My Shelf displays status returned by the server; the app does not schedule recall re-checks.
- Google OAuth is hidden in the embedded client because it needs a native authentication integration. Google sign-in on the external website does not sign in the app. Email/guest availability depends on the existing Firebase project configuration.
- The web client's camera livestream and browser speech recognition are not supported here. Use label photo capture and Home's native voice action instead. Read-aloud availability depends on WebView speech support.
- Chat history remains in memory during navigation; it is not restored after the OS kills the app. Authentication and the watchlist owner reference persist until app data is cleared.
- Live checking needs internet and the existing production API. A missing recall is not proof of safety.
- No Play Store upload, native Firebase Google sign-in, barcode lookup, or cross-device watchlist migration is included.

## Implementation

`bundleWeb` copies an explicit allowlist from `../web` into generated Android assets. It links the Android theme stylesheet and hides Google OAuth in the Android copy only. It does not alter the website sources or include `.env`, deployment logs or server credentials.

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
