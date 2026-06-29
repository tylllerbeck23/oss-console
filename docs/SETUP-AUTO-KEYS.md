# Auto-email a unique license key for every Stripe sale

When a customer pays on Stripe, Stripe pings a small serverless function on your Netlify site,
which **mints a unique license key and emails it to the buyer** (and copies you). No more
minting/emailing by hand. (The manual operator-console flow still works as a backup.)

Files (already in the repo): `netlify/functions/stripe-key.mjs`, `netlify.toml`, `package.json`.

You do **5 short setup steps** — about 15 minutes, one time.

---

### 1. Deploy the site from the GitHub repo (not drag-and-drop)
Functions only deploy when Netlify builds from the repo. In **Netlify → Add new site → Import from GitHub**, pick `tylllerbeck23/oss-console`. Build command: *(leave empty)*. Publish directory: `.`.
(If your current site is drag-and-drop, either switch it to this repo, or create a new site from the repo and point your domain at it.)

### 2. Get an email sender (Resend — free)
- Sign up at **resend.com** (free tier covers a small business).
- Create an **API key** → copy it (`re_…`).
- Sending address: easiest is to **verify your domain** in Resend, then use something like `keys@ossaplication.com`. For a quick test you can use `onboarding@resend.dev` (deliverability is limited — verify a domain before launch).

### 3. Set environment variables in Netlify
**Netlify → Site settings → Environment variables → Add:**
| Key | Value |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_…` (Stripe → Developers → API keys) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` (from step 4) |
| `RESEND_API_KEY` | `re_…` (from step 2) |
| `FROM_EMAIL` | `OSS Console <keys@yourdomain.com>` (optional) |
| `OWNER_EMAIL` | your email for sale copies (optional; defaults to your gmail) |

### 4. Create the Stripe webhook
- **Stripe → Developers → Webhooks → Add endpoint.**
- Endpoint URL: `https://ossaplication.netlify.app/.netlify/functions/stripe-key` *(swap in your real Netlify domain)*.
- Event to send: **`checkout.session.completed`**.
- After creating it, click **Reveal signing secret** → copy the `whsec_…` → paste into `STRIPE_WEBHOOK_SECRET` in Netlify (step 3) → redeploy.

### 5. (Recommended) Map your real Price IDs
Open `netlify/functions/stripe-key.mjs` and fill in `PRICE_TO_PREFIX` with each product's Stripe **Price ID** (Stripe → Products → each price → copy `price_…`). Until you do, it falls back to matching by amount (`$249.99→Fishing`, `$749→SAR`, `$9,999→Fishing kit`, `$11,999→SAR kit`) — which works now but breaks if you change prices.

---

### Test it
- In Stripe, use **test mode** + the test card `4242 4242 4242 4242`, buy through a payment link → you should receive the key email within a few seconds, and a sale copy.
- Or **Stripe → Webhooks → your endpoint → Send test event → `checkout.session.completed`** and check **Netlify → Functions → stripe-key → logs**.

### Notes
- The function mints keys with the **same algorithm the app validates** (`netlify/functions/stripe-key.mjs` mirrors `app.html`). If you ever change `KSALT`/`B32` in the app, change it here too.
- Keys are **not stored server-side** here — to keep your records, the buyer + key also land in your email, and you can still log the sale in the operator console (which is what feeds the profit dashboard).
- Don't commit secrets. They live only in Netlify env vars. `.env` is gitignored.
