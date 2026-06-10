# github-green-graph

Keeps your GitHub contribution graph green every day (Method 2) and lets you
draw custom pixel art text on it (Method 3) — all using real git commits.

---

## How it works

| Feature | How |
|---|---|
| **Daily green** | GitHub Actions commits to this repo at 9 AM UTC every day automatically |
| **Pixel art** | A local Python script backdates commits so your graph spells text |

---

## Step 1 — Create the GitHub repository

1. Go to github.com → **New repository**
2. Name: `github-green-graph`
3. Visibility: **Public** (private repos only show on graph if you enable "Private contributions" in your profile)
4. Do **not** initialize with README (you'll push this folder)

---

## Step 2 — Push this project

Open a terminal in this folder and run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/github-green-graph.git
git branch -M main
git add .
git commit -m "init: github green graph"
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username (e.g. `ausmindeb32`).

---

## Step 3 — Set up secrets (REQUIRED for daily commits to count)

Without this step, the daily commits will be attributed to the wrong email
and **will not appear on your contribution graph**.

1. Go to your repo on GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

| Secret name | Value |
|---|---|
| `GIT_EMAIL` | `ausmindeb32@gmail.com` |
| `GIT_NAME` | `Sasanka` |

---

## Step 4 — Enable workflow write permissions

1. Go to repo **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions** → Save

---

## Step 5 — Trigger the first daily commit manually

1. Go to **Actions** tab in your repo
2. Click **Daily Green Commit** in the left panel
3. Click **Run workflow** → **Run workflow**

From this point forward it runs automatically every day at 9 AM UTC (2:30 PM IST).

---

## Drawing pixel art (Method 3)

Run this **locally** from inside this repo folder.

### Preview first (no commits made):
```bash
python scripts/draw_art.py "SASANKA" --dry-run
```

### Draw the art (commits to local git, then push manually):
```bash
python scripts/draw_art.py "SASANKA" --intensity 3
git push
```

### Draw and push in one shot:
```bash
python scripts/draw_art.py "HIRE ME" --intensity 4 --push
```

### Options:

| Flag | Default | Description |
|---|---|---|
| `--intensity` | 3 | Commits per pixel: 1=light green, 4=darkest green |
| `--col-offset` | 2 | Empty weeks before the text starts |
| `--dry-run` | off | Preview without touching git |
| `--yes` | off | Skip the confirmation prompt |
| `--push` | off | Auto-push after drawing |

### Supported characters:
```
A-Z  0-9  space  ! ? . - +
```

### Maximum text length:
Each character = 5 weeks + 1 gap. With default `--col-offset 2`:
- 52 - 2 = 50 usable weeks → 50 / 6 ≈ **8 characters max**

For longer text, use `--col-offset 1` (gives ~8-9 chars).

### Refreshing art each year:
Commits fall off the graph after 52 weeks. Re-run the script once a year
(around the same time) to redraw. Old art commits become normal history.

---

## File layout

```
.github/workflows/daily-commit.yml   ← runs every day automatically
scripts/draw_art.py                   ← pixel art generator (run locally)
scripts/font_data.py                  ← 5×5 pixel font (A-Z, 0-9, symbols)
activity/log.txt                      ← daily activity log (auto-updated)
activity/streak.txt                   ← current streak count (auto-updated)
activity/art-log.txt                  ← created by draw_art.py when you draw
```
