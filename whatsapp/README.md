# whatsapp/ (Person A)

M12 WhatsApp bot. Forward a product link or a photo of the product or its label; the bot answers "Is it safe? Is it
real?" in English or Hindi, as a text and a voice note. See [MODULES.md](../docs/MODULES.md#m12-whatsapp-bot).

- `bot.py`: the words. Parses the message, picks the reply from the API's verdict (code, not the model), Hindi
  templates, shop-page reading. No network code, fully unit-tested.
- `app.py`: the webhook (`GET`/`POST /webhook`) for the WhatsApp Business Cloud API. Link -> identify + safety +
  trust-check + alternatives; photo -> Gemini reads the label -> identify + safety + alternatives. Voice note:
  Gemini TTS (`gemini-2.5-flash-tts`) -> OGG/Opus with ffmpeg. Each message is one investigation in the API trace
  (`WA-...`).
- Questions (typed, a voice note, a tapped reply button) and PDF manuals go to Shelf Chat (`mode: chat`) as this
  sender (`X-Owner-Ref: wa:<number>`, hashed by the API), so the household list, warranty dates, "my charger gets
  hot", compatibility checks and the manual work on WhatsApp too; the API remembers the conversation. The chat's
  tappable answers become reply buttons (up to 3); support requests and incident reports arrive as their own message.

```bash
cd whatsapp && uv run --python 3.12 pytest -q                     # tests, no network
GOOGLE_CLOUD_PROJECT=project-03d8d835-d5c5-4ad4-bf8 uv run --python 3.12 uvicorn app:app --port 8092
# Without WA_TOKEN/WA_PHONE_ID it runs dry: replies are logged, not sent. Simulate a message:
curl localhost:8092/webhook -H 'content-type: application/json' -d \
  '{"entry":[{"changes":[{"value":{"messages":[{"id":"t1","from":"919800000001","type":"text","text":{"body":"https://demo.safeshelf.app/product/cx-65"}}]}}]}]}'
```

## Going live (needs the Meta test number)

1. developers.facebook.com -> create an app (Business) -> add **WhatsApp** -> note the test **Phone number ID**, a
   **temporary access token** (24 h) or a system-user token, and the app's **App secret** (Settings -> Basic).
   Add your own phone as a test recipient.
2. Store them in Secret Manager: `wa-token`, `wa-phone-id`, `wa-app-secret`, `wa-verify-token` (any random string).
3. `make deploy-whatsapp` (refuses to run until the four secrets exist).
4. In the app's WhatsApp -> Configuration: callback URL `https://<service url>/webhook`, verify token = `wa-verify-token`,
   subscribe to **messages**.

Without `WA_APP_SECRET` the webhook accepts unsigned requests only while it cannot send anything (dry run).
