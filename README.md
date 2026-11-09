# LeetCode Daily Automation Agent

Automated LeetCode problem solver running daily in the cloud via **GitHub Actions**.

## How It Works
- Runs every day at **9:00 AM IST** (3:30 AM UTC) automatically.
- Picks 1–2 unsolved problems (Easy, Medium, Hard).
- Generates optimal solution code via Google Gemini.
- Submits solution directly to LeetCode under your profile.
- Commits generated solution files to the `solutions/` directory and updates `log.csv`.

## Required Repository Secrets
In your GitHub Repository:
Go to **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:

1. `GEMINI_API_KEY`: Your Google AI Studio API key
2. `LEETCODE_SESSION`: Your `LEETCODE_SESSION` cookie from browser DevTools
3. `LEETCODE_CSRF`: Your `csrftoken` cookie from browser DevTools
