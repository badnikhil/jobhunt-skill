# jobhunt — a Claude Code skill for running a real job hunt

A skill that turns Claude Code into a job-hunting agent: it builds a profile of the
candidate, sources openings from public APIs and job platforms, ranks them by genuine
skill fit, generates ATS-safe tailored resumes, submits applications through a browser,
sends paced cold outreach, and maps warm referral paths.

Written from an actual hunt — the failure modes documented here are ones that were hit
and fixed, not hypotheticals.

## Install

```bash
git clone https://github.com/badnikhil/jobhunt-skill
mkdir -p ~/.claude/skills
cp -r jobhunt-skill/skills/jobhunt ~/.claude/skills/
```

Then in Claude Code: `/jobhunt`, or just ask it to help you find a job.

## What's in the skill

| Section | Covers |
|---|---|
| 0 | Learning the candidate — audit their GitHub yourself, find the *rare* skill, correct their self-description |
| 0.5 | **Keep going** — the #1 failure mode is stopping after five applications |
| 1 | Browser automation: geckodriver/Firefox version matching, snap paths, reusing logged-in profiles |
| 2 | Sourcing: Greenhouse/Lever/Ashby/Workday public APIs, and matching source to market |
| 3 | Ranking on skill fit, plus scam detection |
| 4 | Tailored resumes and the ATS ligature trap |
| 5 | Applying, and verifying against ground truth |
| 6 | Cold outreach with pacing that protects the sender |
| 7 | Referral mapping — usually the highest-value step |
| 8 | Platform rules |
| 9–10 | Tracking and honest reporting |

## Three things worth knowing even if you never use the skill

**1. LaTeX resumes silently fail ATS parsing.** Without `\usepackage{cmap}`, the `fi`/`fl`
ligatures have no Unicode mapping, so "profiling" extracts as `proling` and "offline-first"
as `oine-rst`. Every keyword match scores zero and nothing looks wrong. Check with:

```bash
./scripts/check_ats_safe.sh resume.pdf
```

**2. Rank on skill fit, never on pay.** Ranking by stipend meant applying to "Student
Marketing" and "3D Printing" roles that cleared a money threshold. The platform's own fit
rating scored every one of them *Weak*.

**3. Referrals beat volume.** Anyone who has merged your pull requests already has evidence
of your ability. Finding out where they work takes minutes and is worth more than a hundred
cold applications.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/fetch_ats.py` | Pull openings from Greenhouse / Lever / Ashby public APIs |
| `scripts/fetch_workday.py` | Query Workday's public CXS API (most large enterprises) |
| `scripts/browser.py` | Selenium + Firefox helper, incl. snap binary path handling |
| `scripts/check_ats_safe.sh` | Verify a resume PDF survives ATS text extraction |

## Ethics, briefly

The skill declines to build detection evasion, to spam recruiters, or to automate LinkedIn
(their ToS prohibits it and accounts do get banned). Not for decorative reasons — those
things measurably backfire on the candidate. High-volume *tailored* outreach reaches the
same people and actually works.

## Licence

MIT
