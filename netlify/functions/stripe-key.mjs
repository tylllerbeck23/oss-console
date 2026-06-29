// OSS Console — Stripe → auto-issue + email a unique license key per purchase.
// Netlify Function. Endpoint: https://<your-site>/.netlify/functions/stripe-key
// Env vars required (set in Netlify → Site settings → Environment variables):
//   STRIPE_SECRET_KEY      sk_live_…   (Stripe → Developers → API keys)
//   STRIPE_WEBHOOK_SECRET  whsec_…     (from the webhook you create — see docs/SETUP-AUTO-KEYS.md)
//   RESEND_API_KEY         re_…        (resend.com — free tier; or swap for SendGrid/Postmark)
//   FROM_EMAIL  (optional) e.g. "OSS Console <keys@ossaplication.com>" — default uses Resend's test sender
//   OWNER_EMAIL (optional) your email to receive a copy of each sale (defaults to the address below)
import Stripe from 'stripe';
import { randomBytes } from 'node:crypto';

/* ===== license-key algorithm — MUST stay identical to app.html / admin.html ===== */
const KSALT = 'oss7s-2026-key-v1';
const B32 = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';
function keyHash(s){ let h = 2166136261 >>> 0; for (let i=0;i<s.length;i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return ('0000000'+h.toString(16)).slice(-8); }
function algoCheck(prefix, body){ let n = parseInt(keyHash(KSALT+'|'+prefix+'|'+body), 16) >>> 0; let out=''; for (let i=0;i<4;i++){ out += B32[n & 31]; n = Math.floor(n/32); } return out; }
function randBody(){ const u = randomBytes(4); let s=''; for (let i=0;i<4;i++) s += B32[u[i] % 32]; return s; }
function mintKey(prefix){ const b = randBody(); return prefix + '-' + b + '-' + algoCheck(prefix, b); }

/* ===== map a Stripe purchase → edition prefix (which app the key unlocks) =====
   PREFERRED: fill in your real Stripe Price IDs below (Stripe → Products → each price).
   FALLBACK:  matched by the charged amount in cents (works now, but update if you change prices). */
const PRICE_TO_PREFIX = {
  // 'price_ABC123': 'OSS',   // Fishing software
  // 'price_DEF456': 'SAR',   // SAR software
  // 'price_GHI789': 'OSS',   // Fishing Pro Kit (kit includes the Fishing app)
  // 'price_JKL012': 'SAR',   // SAR Responder Kit
};
const AMOUNT_TO_PREFIX = { 24999:'OSS', 74900:'SAR', 999900:'OSS', 1199900:'SAR' }; // fishing sw / SAR sw / fishing kit / SAR kit
const EDITION_NAME = { OSS:'Fishing', SAR:'Search & Rescue', CAP:'CAP' };

function buyerEmailHtml(name, prefix, key){
  const ed = EDITION_NAME[prefix] || 'OSS';
  return `<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:auto;color:#15252f;line-height:1.6">
    <h2 style="margin:0 0 4px">Thanks for your purchase! 🎣</h2>
    <p style="color:#5f7180;margin:0 0 18px">Here is your <b>OSS Console — ${ed}</b> license key.</p>
    <div style="background:#eef5fa;border:1px dashed #0e7490;border-radius:10px;padding:16px;text-align:center;margin:0 0 18px">
      <div style="font:700 22px/1 'Courier New',monospace;letter-spacing:1px;color:#0e7490;word-break:break-all">${key}</div>
    </div>
    <p style="margin:0 0 6px"><b>How to activate</b></p>
    <ol style="margin:0 0 18px;padding-left:20px">
      <li>Open the app: <a href="https://ossaplication.netlify.app/app.html">ossaplication.netlify.app/app.html</a></li>
      <li>Choose the <b>${ed}</b> edition.</li>
      <li>Paste your key once — it activates on that device and works offline, forever.</li>
    </ol>
    <p style="color:#5f7180;font-size:13px;margin:0 0 4px">Install it like an app: open the page → Share → <b>Add to Home Screen</b> (iPhone/iPad) or the <b>Install</b> prompt (Android).</p>
    <p style="color:#5f7180;font-size:13px;margin:0">Keep this key safe — one per device/vessel. Reply if you need any help.<br>— Ocean Surveillance Services</p>
  </div>`;
}

async function sendEmail(to, subject, html){
  if (!process.env.RESEND_API_KEY) { console.warn('RESEND_API_KEY not set — email skipped'); return; }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + process.env.RESEND_API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: process.env.FROM_EMAIL || 'OSS Console <onboarding@resend.dev>', to, subject, html }),
  });
  if (!r.ok) console.error('email send failed', r.status, await r.text());
}

export const handler = async (event) => {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  const sig = event.headers['stripe-signature'];
  const raw = event.isBase64Encoded ? Buffer.from(event.body, 'base64').toString('utf8') : event.body;

  let evt;
  try {
    evt = stripe.webhooks.constructEvent(raw, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (e) {
    return { statusCode: 400, body: 'Webhook signature verification failed: ' + e.message };
  }

  if (evt.type !== 'checkout.session.completed') return { statusCode: 200, body: 'ignored ' + evt.type };

  const session = evt.data.object;
  const email = session.customer_details?.email || session.customer_email;
  const name = session.customer_details?.name || '';

  // which product → which edition
  let prefix = null;
  try {
    const items = await stripe.checkout.sessions.listLineItems(session.id, { limit: 1 });
    const li = items.data[0];
    prefix = PRICE_TO_PREFIX[li?.price?.id] || AMOUNT_TO_PREFIX[li?.amount_total];
  } catch (_) { /* fall through */ }
  prefix = prefix || AMOUNT_TO_PREFIX[session.amount_total] || 'OSS';

  const key = mintKey(prefix);

  if (email) await sendEmail(email, 'Your OSS Console license key', buyerEmailHtml(name, prefix, key));

  // owner copy / sale notification
  const owner = process.env.OWNER_EMAIL || 'tylerdeanbeck@gmail.com';
  await sendEmail(owner, `💰 Sale — OSS ${EDITION_NAME[prefix]||prefix} — ${email||'no email'}`,
    `<p>New sale.</p><p><b>Product:</b> ${EDITION_NAME[prefix]||prefix}<br><b>Buyer:</b> ${name} &lt;${email||'?'}&gt;<br>` +
    `<b>Amount:</b> ${(session.amount_total/100).toLocaleString('en-US',{style:'currency',currency:(session.currency||'usd').toUpperCase()})}<br>` +
    `<b>Key issued:</b> ${key}</p>`);

  return { statusCode: 200, body: 'key issued + emailed: ' + key };
};
