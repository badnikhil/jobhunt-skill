---
name: jobhunt
description: Run a real job or internship hunt end to end - build a candidate profile, source openings from public APIs and job platforms, rank them by genuine skill fit, generate ATS-safe tailored resumes, submit applications through a browser, send paced cold outreach, and map warm referral paths. Use when someone asks for help finding a job or internship, applying at volume, tailoring a resume for ATS, or automating job applications.
---

# Job Hunt

A complete pipeline for finding and winning software roles. . Everything below was learned the hard way — the failure
modes are as important as the happy paths.

---

## 0. FIRST: learn the candidate properly. Do not skip this.

**The quality of every later step depends on how well you know the person.** A generic
resume and a generic email get generic results. Spend real effort here before anything else.

Gather, and write it to `jobhunt/PROFILE.md`:

| What | Why it matters |
|---|---|
| **Verified GitHub history** | Merged PRs *to repos they don't own* are the real credential. Count them per org. |
| Education, year, graduation year | Decides eligibility. "New Grad 2027" excludes a 2028 graduate. |
| Location + willingness to relocate/remote | Filters most listings |
| Prior roles, with dates and real accomplishments | Watch for gaps; know how to present them |
| Rare/differentiating skills | This is the whole game — see below |
| Salary floor, time available, hard deadlines | Prevents wasted applications |
| Anything they want **excluded** | Past employers with poor reputation, personal projects — ask explicitly |

### Audit their GitHub yourself; don't take their word for it

```bash
curl -s "https://api.github.com/search/issues?q=author:USER+is:pr+is:merged&per_page=100" \
  | python3 -c "import json,sys;from collections import Counter
d=json.load(sys.stdin)
ext=[i for i in d['items'] if not i['repository_url'].endswith('/USER')]
print('merged PRs to others repos:',len(ext))
print(Counter('/'.join(i['repository_url'].split('/')[-2:]) for i in ext).most_common())"
```

**Expect the headline number to be inflated.** Profile PR counts routinely include
auto-generated commits to their own repos. Find the *externally merged* count — that is
the number worth citing, and citing an inflated one invites a credibility hit when a
reviewer clicks through.

**Correct their self-description where the evidence disagrees.** People routinely
mis-describe their own best work — naming the umbrella foundation instead of the actual
project, or leading with the impressive-sounding thing rather than the rare thing.
Find what is genuinely scarce in their background and lead with that everywhere.

### Find the rare skill and build the hunt around it

Most candidates are interchangeable. Look for the thing almost nobody else has —
compiler contributions, kernel work, GPU programming, a shipped OS, real distributed-systems
implementation. Then target companies that specifically need it. **A rare skill turns a
volume game into a targeted one**, and targeted converts far better.

---

## 0.5 KEEP GOING. Do not stop after a handful.

**This is the most common way this skill fails.** An agent sources some listings, sends five
applications, writes a nice summary, and stops. That is worthless. A job hunt is a volume
game with a quality floor, and it runs for weeks.

### The rule

**Never end a turn having applied to "a few".** If there is queue left and no blocker, keep
applying. Do not stop to ask whether to continue — you were already asked to run the hunt.
Report progress *and keep working* in the same turn.

### How to actually sustain it

- **Batch, don't trickle.** Run 50–80 applications per batch, in the background:
  `nohup python3 apply.py --n 60 --submit > log 2>&1 &`. A batch takes ~25 minutes; do other
  work while it runs.
- **Never idle waiting.** While a browser batch runs, do HTTP-only work — pull more listings,
  discover hiring emails, research companies, build the next queue. There is always a
  non-browser task available.
- **When a source runs dry, find another.** Exhausted one platform? Move to the next. Out of
  platforms? Switch to direct company outreach. Out of companies? Map referrals. Out of
  those? Go back and re-scrape — boards refresh daily and new postings appear constantly.
- **Re-scrape on a cadence.** Yesterday's queue is stale. Job boards add listings every day;
  a hunt that only ever processes the first pull is leaving most of the market untouched.
- **Keep a permanent ledger** so re-runs skip what's done and only new listings get applied to.
  This makes continuous re-scraping cheap and safe.
- **Parallelise research with subagents** where available — sourcing, email discovery,
  company research and referral mapping are all independent and can run at once.

### What legitimately stops you

Only these:
1. The user says stop.
2. A hard blocker needing them — a login, a CAPTCHA, a decision only they can make.
   Say exactly what you need, and **keep working on everything that isn't blocked** meanwhile.
3. A daily rate cap you set for safety (e.g. the email-per-day limit). Cap reached on one
   channel means switch channels, not stop.
4. The queue is genuinely empty *and* re-scraping produced nothing new — which almost never
   happens on the same day.

### What is NOT a reason to stop

- "I've applied to a reasonable number." There is no reasonable number; there is the queue.
- "I should check whether the user wants more." They asked for a job hunt.
- "The remaining listings are lower quality." Then say so, apply the quality floor, and
  keep going through what clears it.
- "I finished the batch I planned." Plan the next one and run it.

### But do not pad the numbers

Persistence means *finding more real opportunities*, never lowering standards to inflate a
count. Applying to junk wastes the candidate's time, damages their reputation with the
platforms, and buries genuine leads. If quality drops below the floor, go find a better
source — do not scrape the barrel and call it volume.

---

## 1. Environment: browser automation

### Setup (Linux, Firefox or chrome)

```bash
python3 -m pip install selenium
# geckodriver MUST match the Firefox major version, or you get cryptic session errors
curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest \
 | grep -o 'https[^"]*linux64.tar.gz' | head -1 | xargs curl -sL -o gd.tar.gz
tar xzf gd.tar.gz
```

**Snap-packaged Firefox needs an explicit binary path** or you get
`binary is not a Firefox executable`:

```python
opts.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
```

### Reuse the candidate's logged-in sessions

Job sites need auth. Clone their Firefox profile rather than handling passwords:

```bash
SRC=~/snap/firefox/common/.mozilla/firefox/*.default   # or ~/.mozilla/firefox/*.default
mkdir -p jobhunt/fxprofile
for f in cookies.sqlite cookies.sqlite-wal permissions.sqlite prefs.js key4.db logins.json cert9.db; do
  cp -a "$SRC/$f" jobhunt/fxprofile/ 2>/dev/null; done
```

Then `opts.add_argument("-profile"); opts.add_argument(".../fxprofile")`.

- **Tell the user plainly** that this copies their cookies and live sessions, and that it
  stays local.
- **Never run it against a profile that Firefox currently has open** — profile lock.
- Check which sites they're actually logged into by reading `cookies.sqlite` hosts.
- **Only one browser at a time** can hold the profile. Sequence browser work; do HTTP-only
  work (API pulls, email discovery) in parallel instead.

### Headed vs headless

Run **headed** when a login, CAPTCHA or OAuth consent is needed — the user completes it
while your script polls for success. Everything else headless. Gmail is memory-heavy:
**use a fresh driver per email** or the session dies mid-batch with `InvalidSessionIdException`.

---

## 2. Sourcing openings

### Public ATS APIs — no scraping, no login

```python
# Greenhouse
f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
# Lever
f"https://api.lever.co/v0/postings/{company}?mode=json"
# Ashby
f"https://api.ashbyhq.com/posting-api/job-board/{company}"
# Workday (POST JSON) — used by most large enterprises
f"{base}/wday/cxs/{tenant}/{site}/jobs"
   body: {"appliedFacets":{},"limit":20,"offset":N,"searchText":"intern"}
```

Workday tenant/site come from the careers URL: `https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite`
→ tenant `nvidia`, site `nvidiaexternalcareersite`. A wrong site name returns HTTP 422.

### Job platforms

Most platforms render server-side and parse fine with BeautifulSoup; some are JS-only and
need the browser. Test with a plain `curl` first — if you get a 20 KB shell, it's JS-rendered.

### Reality check on where roles actually live

**Match the source to the candidate's market.** In one real hunt, US startup ATS boards
yielded 1,876 postings of which **5 were genuinely junior** — all US-based. The candidate
was in India, where internships live on local platforms and company career sites instead.
**Survey first, then commit.** Pulling thousands of irrelevant listings feels productive
and is not.

Also check **seasonality**: large employers open campus/intern cycles at fixed times.
If the cycle is closed, note the reopening month in the tracker and move on — don't
conclude the company doesn't hire.

---

## 3. Ranking — rank on skill fit, never on money

```python
JUNK   = r"wordpress|shopify|seo|content|social media|telecall|data entry|sales|marketing"
SENIOR = r"senior|staff|principal|lead|manager|director|head of|architect|sr\."
JUNIOR = r"intern|trainee|apprentice|new ?grad|graduate|entry|junior|fresher"
STRONG = r"<the candidate's actual stack>"
```

**Hard-won lesson:** an early batch ranked by stipend and applied to "Student Marketing"
and "3D Printing" roles because they cleared a money threshold. The platform's own fit
rating scored every one of them **Weak**. Rank on skill match; use pay only as a floor.

**Always set a pay floor** (e.g. skip anything below a stated minimum, and skip unpaid
roles entirely unless the candidate says otherwise). A title-only filter will happily
apply to unpaid work.

### Scam and time-waster detection — filter these out

| Signal | Meaning |
|---|---|
| Apply link goes through a **URL shortener** (`rb.gy`, `bit.ly`) | Lead-generation or worse. Legitimate employers link to their own site or an ATS. |
| **Identical stipend** across many unrelated "companies" | Posting mill, same operator behind all of them |
| **Implausible pay** for a junior remote role | Fake. One posted five simultaneous roles at ~10x market. |
| "Registration fee", "training fee", "security deposit" | Scam, unconditionally |
| Unpaid, when the candidate needs income | Counterproductive regardless of legitimacy |

Log what you excluded and why. The user should be able to audit your judgement.

---

## 4. Resumes: tailored variants, and the ATS trap

Build one variant per role family (backend / fullstack / ai / mobile / devops / systems).
**Only reorder and re-emphasise real experience. Never invent a skill to match a posting.**

### The ligature bug — check this every single time

LaTeX PDFs silently drop `fi`, `fl`, `ffi` ligatures during text extraction, so an ATS
searching for "profiling" or "offline" sees `proling` and `oine` and scores zero.
**This silently sinks every application and nothing visibly looks wrong.**

```latex
\usepackage[T1]{fontenc}
\usepackage{cmap}      % <- this is the fix
\usepackage{lmodern}
```

Verify after every build:

```bash
pdftotext resume.pdf - | grep -oE '\b(oine|proling|specic|ows|rst|dierent|conguration)\b'
# any output at all = broken. Must return nothing.
```

If `cmap.sty` is missing, fetch it:
`curl -sL https://mirrors.ctan.org/macros/latex/contrib/cmap/cmap.sty -o ~/texmf/tex/latex/local/cmap.sty && texhash ~/texmf`

### Other ATS rules

- **No tables for skills** — many parsers mangle multi-column layouts. Plain `Label: a, b, c` lines.
- Standard headings: Technical Skills / Experience / Projects / Education.
- One page for juniors.
- Always confirm the PDF extracts cleanly: `pdftotext resume.pdf - | head -40`.

---

## 5. Applying

Write one applier per platform. Structure that survives contact with reality:

1. Skip anything already applied to (**keep a permanent URL ledger** — re-runs must never double-apply).
2. Open the listing, find the apply control **by reading actual button text**, not by
   substring-matching page body text (that gives false positives from sidebars).
3. Fill availability radios, screening questions, cover-letter textareas.
4. Attach the matching resume variant.
5. Submit — then **verify against ground truth**, not the submit click.

### Verify properly

Never trust "I clicked submit". Confirm on the platform:
- Re-open the listing and check it now shows as applied, or
- Read the candidate's applications list.

Beware: **application-list pages often cap or paginate**, so absence there is not proof of
failure. In one run 27 applications looked unverified on the list page but every single one
showed "applied" on its own listing page. **Check the per-listing state before concluding
anything failed.**

### Run long batches in the background

`nohup python3 apply.py --n 60 --submit > log 2>&1 &` — a 60-application batch takes
~25 minutes. Python buffers stdout when redirected, so use `flush=True` on prints you
want to watch live.

---

### Platform gotcha: Unstop native forms (Angular)

- Profile-prefilled dropdowns (Domain / Course / Course Specialization) must **never** be touched. A generic
  `div[class*=select]` selector also matches *empty inner wrappers* of those dropdowns; clicking one opens it,
  a "pick the first option" fallback selects the alphabetically-first value (Acoustics Engineering, MBA, HRM…),
  and Angular then resets Graduating Year → the form fails with "Please select year of graduation".
- Scope screening-question dropdowns to elements **after** the "Screening Questions" heading in DOM order:
  `//*[text()='Screening Questions']/following::*[...]`. An `ancestor::*[contains(.,'Screening Questions')]`
  guard is useless — it matches the whole form container.
- After any dropdown work, re-assert the chips (Graduating Year is `label.un-label` with class `label-checked`).
  Verify state through the DOM (`input.checked`), never by guessing from class names like `active`.
- Success = URL contains `register/success?rstatus=1`. `register/success?source=external` is an external
  redirect, not a submission — put those on the manual list with the real destination URL.
- When a form keeps failing, **dump the widget's actual DOM** before iterating on selectors.
- Unstop keeps a **per-opportunity form draft**: a buggy run's drift persists in that listing's draft even
  when the profile is fine. Restore profile-derived fields before every submit.
- Specialization is Angular Material: click the `mat-select` (not the `mat-form-field` wrapper); options live in
  `.cdk-overlay-pane mat-option`, which is `position:fixed` — `offsetParent` checks see nothing, use Selenium
  `is_displayed()`; fallback to mat-select typeahead via `send_keys`.
- Chip radios are `<div class="un-radio"><input><label class="un-label">` with no `for`: click the **input** and
  verify `.checked`. A **disabled** graduation-year input means the listing is final-year-only → mark ineligible.
- Eligibility is signalled three ways, all terminal: a modal ("You are not eligible … Domain"), a location
  gate ("Since you're not located in <city>, you can't apply"), and disabled year chips. Never click
  "Update profile" to force eligibility.
- "Expected Compensation (in LPA)" is numeric (≤100). Answer with a number; text fails validation silently.
 Three blind
  retries cost more than one inspection.

---

### Platform gotcha: Wellfound (on-platform apply)

- Login is Google/magic-link → do it in the user's normal browser, then copy cookies (+ the `-wal` file) into
  the automation profile **while holding the profile lock**, or a browser that's mid-run writes stale cookies back.
- Listing page: `button` "Apply"/"Apply now" opens a modal; custom questions are
  `textarea[name^='customQuestionAnswers']`; submit is `[data-test='JobApplicationModal--SubmitButton']`.
  Ground truth for success: reload the listing and look for a `button` reading "Applied".
- Location qualification ("This job does not support the locations on your profile"): radios
  `qualification.location.action` (living_in / relocate_to) plus a **react-select** city picker whose placeholder
  div intercepts clicks — click the radio's `<label>`, `focus()` the input via JS, type the city, click
  `.select__option`. The textarea and submit stay disabled until both are set.
  The radios are custom-styled and **visually hidden**: Selenium `is_displayed()` is False, so any
  displayed-filter drops them silently. Query without the filter and click `r.closest('label')` via JS. Scope
  these lookups to the document — the submit button's nearest container excludes the qualification block.
- "Rate limit" appearing in a job description is not a throttle. Match real throttle phrasing only
  (`you've reached … limit`, `too many requests`, HTTP 429), and only in the top of the page.
- "no longer accepting" = closed; record it as terminal so re-runs skip it.
- Title filters must catch `product management`, `GTM`, `growth`, `founder's office` — "product manager" alone
  lets "Product Management Intern" through.
- Pace: 15–35 s between applications; ~40 per batch with per-job ledger writes went through without any throttle.

### Direct ATS forms (Greenhouse / Ashby / Lever) — where the good companies are

- Source real-company roles from the public ATS APIs (`boards-api.greenhouse.io`, `api.lever.co`,
  `api.ashbyhq.com`) and curated GitHub lists (speedyapply `2026-SWE-College-Jobs` INTERN_INTL / NEW_GRAD_INTL
  carry India rows; parse the *apply* link column, not the company homepage). `\bintern\b`, not `intern` —
  otherwise "Internal Audit" floods the results.
- **Greenhouse and Ashby use invisible reCAPTCHA and go through from a headless browser; Lever shows a visible
  challenge and does not** — Lever goes on the manual list with pre-written answers.
- Greenhouse: country/location/school/degree are react-select flyouts — match options with `startswith`
  ("India" must not pick "British Indian Ocean Territory"); own-site embeds (kaseya.com) use native `<select>`s
  and **ignore synthetic clicks** — use a real ActionChains click and poll ~25 s. Refuse to submit when a
  required question is unmapped. Never let a first-option fallback answer an honesty question (relocation,
  authorization) — map them explicitly and truthfully.
- Ashby: `_systemfield_*` inputs; resume autofill pre-types Location as plain text that fails validation — clear
  and re-select from `div[role=option]`; blur the dropdown before Submit or the click is swallowed; yes/no
  button groups and radios are answered by question text (SMS consent sits under the "Phone number" question).
- Verify with the ATS receipt email (`no-reply@us.greenhouse-mail.io`, `no-reply@ashbyhq.com`) — never by
  re-submitting; a silent form can already have gone through.

### Platform gotcha: Workday (big-company portals)

- Flow: `/apply` → "Apply Manually" → Create Account (per tenant; store the generated password locally) →
  My Information → My Experience → Application Questions → Voluntary Disclosures → Review. Drafts persist on
  the account, so a re-run resumes where it left off — and re-adds entries unless you delete existing ones first.
- Inputs are keyed by **`id`** (`name--legalName--firstName`, `address--city`, `phoneNumber--phoneNumber`,
  `source--source`), not `data-automation-id`. `is_displayed()` is unreliable — test `offsetParent` and rect.
  Every interaction re-renders: re-find elements per action.
- Prompts ("How did you hear about us", field of study, skills): click the field, type into the popup's own
  `#searchBox`, ArrowDown, Enter, then **Tab**. Escape cancels the pick; typing + Enter on the field itself
  navigates away; clicking the "My Information" heading hits the progress-bar step link and reloads the step.
- Custom checkboxes are visually hidden — click the label via JS and verify `is_selected()`. Use real
  (ActionChains) clicks for Save and Continue; errors appear as "Error-<Field>" buttons.
- **Resume upload returns HTTP_500 for automated sessions** (every tenant, every file, native and DataTransfer
  paths). Don't disguise the browser. Hand off instead: automation completes pages 1–2, the candidate attaches the
  resume and finishes pages 3–5 in about two minutes per posting.
- `sleep`-based schedulers stall through laptop suspend; check elapsed time and relaunch by hand.

## 5.5 The manual-apply list — for everything automation shouldn't touch

Not every application should be automated, and some must not be. Rather than skipping those,
**hand the candidate a ready-to-click list** so the work still gets done — by them, in thirty
seconds each, with zero account risk.

### When a role belongs on the manual list

- **The platform prohibits automation** (LinkedIn is the big one — their ToS bans bots and
  they do restrict accounts). Scrape listings read-only, then hand over the links.
- **The application needs judgement** — essay questions, "why this company", portfolio picks.
- **High-value roles** where a careless auto-fill would waste a rare opportunity.
- **OAuth or CAPTCHA walls.** Google refuses OAuth from WebDriver-controlled browsers outright
  ("This browser or app may not be secure"), so anything behind Google sign-in is manual.
- **Anything the candidate said to leave alone.**

### The format that actually gets used

A single `MANUAL-APPLY.md`, one row per role, with **the exact resume file named** — so there
is no thinking required, just click and attach:

```markdown
| # | Company | Role / why it fits | Location | Resume to attach | Link |
|---|---------|--------------------|----------|------------------|------|
| 1 | Acme    | Compiler Engineer — matches your LLVM PRs | Pune | `resumes/resume-systems.pdf` | [apply](url) |
```

Include, above the table, a small index of every resume variant and what it's for. The whole
point is that the candidate opens the file and starts clicking without having to decide anything.

### Rules for the list

- **Name the specific resume file per row.** "Use the systems one" is friction; a path is not.
- **Say why each role fits** in a few words. It tells them where to spend effort when the
  list is long, and it becomes the first line of their cover note.
- **Sort by expected value, not by source.** The one role where they're a rare fit belongs
  above fifty where they're one of a thousand.
- **Include a dead-ends section.** Companies that are bankrupt, acquired, domain-hijacked,
  visa-gated, or whose "careers" address is actually an anti-fraud inbox. Saving them from
  wasted applications is as valuable as finding good ones — and stops them rediscovering
  the same dead ends next week.
- **Note eligibility traps explicitly.** Graduation-year gates, "final year only",
  citizenship requirements, lifetime bars from other programmes.
- Keep it in the same folder as the resumes so paths resolve.

### Tell them plainly which is which

When reporting, separate "I applied to N" from "here are M for you to click". Conflating the
two overstates what's been done. And be honest about relative value: a manual application to
a company where their background is rare will usually beat a hundred automated ones.

---

## 6. Cold outreach — high value, easy to get wrong

Direct email to a real hiring address beats an ATS submission, because a human reads it.

### Finding addresses — only published ones

Scan `/careers`, `/jobs`, `/contact`, `/about`, `/join-us` and the footer. Keep
`careers@ jobs@ hiring@ hr@ talent@ people@`. Reject image files, `noreply@`, and
placeholder addresses from form examples (`name@company.com`, `your@mail.com`).

**Never** guess addresses from naming patterns you didn't observe, harvest individual
employees' personal emails, or use permutation tools. Prioritise companies whose careers
page **explicitly invites speculative applications** — they've asked for it.

### Writing them

Each email must be genuinely specific: name what the company builds and why this
candidate matches. **Reference concrete artifacts** — PR numbers, repos, measured results.
Templates get deleted.

### Pacing — this protects the candidate

```python
MAX_PER_DAY = 45              # bulk sending gets Gmail accounts flagged
GAP_SECONDS = (150, 420)      # randomised 2.5-7 min between sends
```

Keep a permanent ledger keyed on address so nobody is mailed twice — and **write it after
every single send**, not at the end of the run. A crash mid-batch otherwise causes duplicates.

**Say no to spamming.** If asked to blast identical mail at recruiters, explain the actual
cost: recruiters share spammer names, Gmail reputation damage sends *all* their mail to
spam including the good ones, and it burns the best channel they have. Offer high-volume
*tailored* outreach instead — that reaches the same number of people and actually works.

### Sending via Gmail

The compose URL is far more reliable than driving Gmail's obfuscated DOM:

```python
url = ("https://mail.google.com/mail/?view=cm&fs=1&tf=1"
       f"&to={quote(to)}&su={quote(subject)}&body={quote(body)}")
```

Attach through the hidden `input[type=file]`; wait for the filename to appear in the page
before clicking Send. Verify afterwards in the Sent folder.

---

## 7. Referral mapping — usually the highest-value step

**Do this early. It routinely beats hundreds of cold applications.**

Anyone who has **reviewed or merged the candidate's code already has evidence of their
ability**. Find them:

```bash
gh api repos/OWNER/REPO/pulls/NUMBER --jq '.merged_by.login'
```

Then check public GitHub profiles for `company`. In a real hunt this surfaced a maintainer
who had merged the candidate's PR and worked at a major cloud provider — while also
mentoring the open-source org the candidate contributed to. That is a warm introduction
that no amount of cold applying replicates.

Rank honestly: someone who merged twelve PRs is a strong referral; someone who left one
drive-by comment is not. **The candidate sends these themselves** — never automate a
personal referral request.

---

## 8. Platform rules — respect them, and say so

- **LinkedIn prohibits automated access and does ban accounts.** Their professional
  presence is an asset. Prefer: scrape listings read-only, or build a **manual-apply list**
  (link + which resume variant to use) that they click through themselves.
- Never build detection evasion. If asked to hide automation, decline that specific part
  and explain the practical cost — accounts get restricted and applications get binned.
  Do the legitimate high-volume version instead.
- Where a platform's own policy permits AI assistance **with disclosure**, disclose.
- Some employers explicitly reject pre-application PRs. Check before "contributing to get noticed".

---

## 9. Tracking

Maintain `jobhunt/APPLICATIONS.md`:

- Every application: date, company, role, pay, source, which resume, status, link
- Every email: recipient, date, resume attached, verified-sent
- **What you excluded and why** — scams, off-target, unpaid
- **Pipeline**: cycles not open yet, with the month to check back
- **Follow-ups** with dates

Status vocabulary: `applied → ack → oa → interview → offer / rejected / ghosted (30d)`

---

## 10. Reporting to the user

- **Report verified counts, never assumed ones.** "27 submitted, 27 confirmed on listing pages."
- **Surface your own mistakes immediately** — a wrong filter that applied to unpaid roles,
  a duplicate email, a false-negative verification. They compound silently otherwise.
- **Say when the data contradicts the plan.** If the target market has nothing open, say so
  and pivot rather than manufacturing activity.
- Volume is not the goal. One warm referral or one well-matched application outperforms
  a hundred sprayed ones, and the user deserves to hear that even when they asked for volume.
