# OSS Console — De-"AI" design + ad notes

From verified deep-research (2026-06-25, run wry9lgwkb). **Honesty flag:** the *design direction* below is corroborated, but almost every **quantified conversion-lift %** and the **"real vs AI footage" trust stats** were **refuted in verification** — use the direction, don't quote numbers, and treat "favor real footage" as judgment, not a proven stat.

## A. De-AI checklist (what makes a site look AI-generated, and the fix)

**Where OSS already wins:** the two biggest AI tells are **Inter font** + **purple/indigo→blue gradients**. OSS uses **Saira + JetBrains Mono** and **teal/navy** — so it already dodges both. (Note: "Inter is THE tell / a two-font swap is the #1 fix" was *refuted* — don't overweight fonts.)

**Highest-confidence fixes (3-0 verified) — do these:**
- [ ] **One type+spacing system on a 4px/8px baseline grid.** Every margin/padding/gap is a multiple of 4 or 8 (4,8,12,16,24,32…); line-height drives the rhythm. This systematic consistency is the single biggest "deliberate, not templated" signal. → audit `app.html`/`index.html` for off-grid paddings.
- [ ] **Use spacing to encode relationships (Gestalt proximity):** tighter gaps between related items, bigger gaps between unrelated groups. Don't space everything evenly.
- [ ] **Real proof, framed as specific operational outcomes** (e.g. "covered 80 acres on one battery," "found a drifting kayaker in 6 min") — *once you have real users/results*. Vague praise reads as filler.
- [ ] **No fabricated testimonials/reviews — legal, not just taste.** FTC Consumer Reviews & Testimonials Rule (effective Oct 21 2024) allows civil penalties (~$51.7k/violation) for fake reviews/testimonials. Until real customers exist, use capability statements, not invented quotes.

**Medium-confidence fixes — worth doing:**
- [ ] **Replace emoji-as-icons with a consistent set of real SVG line icons** across the app + site. (Caveat: the strict "all icons same size / never mix filled+stroked" rule was *weakly* supported — aim for consistency, don't obsess.) This is the core of the user's "un-claude it."
- [ ] **Kill layout sameness.** The AI skeleton = hero → 3 identical icon cards → testimonials → pricing, reused everywhere. Vary section structure; the OSS home already breaks this with the animated detection hero + kits — keep diversifying.
- [ ] **Real screenshots over stock/generic visuals** — the interface itself is the trust signal. Use real app screen-recordings + (later) real drone footage. The home "See it in action" slot is reserved for exactly this.
- [ ] **Semantic color tokens** named by function (`--action-primary`, `--ok`, `--warn`) — OSS mostly does this already.

## B. Ad / marketing plan

**Strongest verified guidance = the hook.** Land the core message in the **first frame and first ~3 seconds** (only ~25% watch past 5s; ~60%+ of top-CTR videos deliver the point in 3s). Open on the payload: a fish lighting up under a targeting box, or "find a person in the water in minutes."

**AI vs real footage — reasoned judgment (NOT a proven stat):** every statistic claiming real/authentic footage out-converts AI was refuted. So the call rests on: (1) the verified "real interface/imagery is the trust signal" principle, (2) the FTC no-fake-proof rule, (3) a gear/outdoors/safety market rewards *demonstrable real capability*. → **Don't fake aerial fish footage with AI.** Use real app captures now; film the real "drone finds fish" money-shot once the drone arrives.

**Prioritized production plan (solo founder):**
1. **Now (assets on hand):** 15–30s ad from **screen-recordings of the app + the demo page** + a few stills. Narration: **your own voice** (authentic) or a clean TTS. Tools: OBS/QuickTime (capture), CapCut/DaVinci Resolve (free edit). ~$0.
2. **Now:** cut 9:16 vertical for Reels/TikTok + 16:9 for YouTube; hook-first. Run small Meta/IG + YouTube tests with **tracked links** (use the operator-console UTM builder).
3. **After the drone arrives:** capture real aerial fish-spotting / SAR b-roll → re-cut a hero ad with the money-shot; drop it into the home "See it in action" slot.

_Sources: designsystems.com & designary (spacing/baseline grid, 3-0), 925studios/dev.to/UX Planet (AI-tell patterns, medium), FTC Reviews & Testimonials Rule (3-0), TikTok/short-video hook mechanics (3-0). Refuted: all specific conversion-lift % and real-vs-AI-footage trust stats — see run wry9lgwkb caveats._
