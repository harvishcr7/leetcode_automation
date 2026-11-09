"""
LeetCode Daily Agent - everything in one file.

SETUP
  1. pip install requests python-dotenv (and anthropic if using Claude)
  2. Put your keys in .env or the SETTINGS block below:
     - GEMINI_API_KEY (from Google AI Studio) or ANTHROPIC_API_KEY
     - Optional for Auto-Submit: LEETCODE_SESSION and csrftoken (from browser cookies)
  3. Test:   python leetcode_agent.py      (AUTO_SUBMIT = False only saves solutions)
  4. Go live: set AUTO_SUBMIT = True, then schedule it daily at 9 AM
       Windows: Task Scheduler -> run `python leetcode_agent.py` from this folder
       Mac/Linux: crontab -e -> 0 9 * * * cd /path/to/folder && python leetcode_agent.py

OUTPUT: solutions/ folder (one file per problem) and log.csv (date, problem, result).
"""
import csv
import html
import os
import random
import re
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ======================= SETTINGS (edit these) =======================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "PASTE_LEETCODE_SESSION_COOKIE")
LEETCODE_CSRF = os.getenv("LEETCODE_CSRF", "PASTE_CSRFTOKEN_COOKIE")
LANG = os.getenv("LEETCODE_LANG", os.getenv("PROGRAMMING_LANG", "java")).lower()
if LANG not in ("java", "python3", "cpp", "javascript", "golang", "csharp", "typescript"):
    LANG = "java"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
AUTO_SUBMIT = os.getenv("AUTO_SUBMIT", "True").lower() in ("true", "1", "yes")
MAX_RETRIES = 2             # retries with error feedback if a submission fails

# Email Notification Settings
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "harvishvarshanrk@gmail.com")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
# =====================================================================

EXT = {"python3": "py", "java": "java", "cpp": "cpp", "javascript": "js",
       "typescript": "ts", "golang": "go", "csharp": "cs"}

BASE = "https://leetcode.com"
http = requests.Session()
http.headers.update({
    "Cookie": f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={LEETCODE_CSRF}",
    "x-csrftoken": LEETCODE_CSRF,
    "Content-Type": "application/json",
    "Referer": BASE + "/problemset/",
    "Origin": BASE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
})

LIST_Q = """query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
    questions: data { frontendQuestionId: questionFrontendId title titleSlug difficulty status paidOnly: isPaidOnly }
  }
}"""
DETAIL_Q = """query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) { questionId title content codeSnippets { langSlug code } }
}"""


def gql(query, variables):
    r = http.post(f"{BASE}/graphql", json={"query": query, "variables": variables}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def hard_solved_this_week():
    """Check log.csv to see if a HARD problem was already accepted this calendar week."""
    log_file = Path("log.csv")
    if not log_file.exists():
        return False
    now = datetime.now()
    cur_year, cur_week, _ = now.isocalendar()
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("difficulty", "").upper() == "HARD" and row.get("status") == "Accepted":
                    row_dt = datetime.fromisoformat(row.get("date", ""))
                    if row_dt.isocalendar()[:2] == (cur_year, cur_week):
                        return True
    except Exception:
        pass
    return False


def pick_difficulty(is_first=True):
    now = datetime.now()
    # 1 HARD question per week (scheduled on weekend: Saturday=5 or Sunday=6)
    if is_first and now.weekday() in (5, 6) and not hard_solved_this_week():
        return "HARD"
    # Rest of the week: mix of Easy (60%) and Medium (40%)
    return "EASY" if random.random() < 0.60 else "MEDIUM"


def pick_question(is_first=True):
    difficulty = pick_difficulty(is_first=is_first)
    status = "NOT_STARTED"
    data = gql(LIST_Q, {"categorySlug": "", "skip": 0, "limit": 100,
                        "filters": {"difficulty": difficulty, "status": status}})
    qs = [q for q in data["problemsetQuestionList"]["questions"] if not q.get("paidOnly") and q.get("status") != "ac"]
    if not qs:
        # Fallback without status filter if needed
        data = gql(LIST_Q, {"categorySlug": "", "skip": 0, "limit": 100,
                            "filters": {"difficulty": difficulty}})
        qs = [q for q in data["problemsetQuestionList"]["questions"] if not q.get("paidOnly") and q.get("status") != "ac"]
    if not qs:
        raise RuntimeError(f"No unsolved {difficulty} questions found.")
    return random.choice(qs), difficulty


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def clean_code(text):
    text = text.strip()
    match = re.search(r"```(?:[a-zA-Z0-9]*\n)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return re.sub(r"^```[a-zA-Z0-9]*\n?", "", text).rstrip("`").strip()


def ask_gemini(messages):
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    models_to_try = [
        GEMINI_MODEL,
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest",
        "gemini-3.8-flash"
    ]
    models_to_try = list(dict.fromkeys(models_to_try))

    last_error = None
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(url, json={"contents": contents}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    return clean_code(text)
            elif resp.status_code in (404, 429, 500, 503):
                last_error = f"{resp.status_code} on {model_name}: {resp.text}"
                time.sleep(1)
                continue
            else:
                resp.raise_for_status()
        except requests.RequestException as e:
            last_error = f"Exception on {model_name}: {e}"
            time.sleep(1)
            continue

    raise RuntimeError(f"Gemini API request failed across models: {last_error}")


def ask_claude(messages):
    import anthropic
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = claude.messages.create(model=ANTHROPIC_MODEL, max_tokens=4000, messages=messages)
    return clean_code(resp.content[0].text)


def ask_llm(messages):
    global GEMINI_API_KEY
    # Check if Gemini key is set or starts with AQ./AIza
    if GEMINI_API_KEY or (ANTHROPIC_API_KEY and (ANTHROPIC_API_KEY.startswith("AQ.") or ANTHROPIC_API_KEY.startswith("AIza"))):
        if not GEMINI_API_KEY:
            GEMINI_API_KEY = ANTHROPIC_API_KEY
        return ask_gemini(messages)
    elif ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "PASTE_ANTHROPIC_KEY":
        return ask_claude(messages)
    else:
        raise RuntimeError("No API key configured. Please set GEMINI_API_KEY or ANTHROPIC_API_KEY in .env.")


def submit_and_wait(slug, question_id, code):
    headers = {"Referer": f"{BASE}/problems/{slug}/", "Origin": BASE}
    for attempt in range(3):
        r = http.post(f"{BASE}/problems/{slug}/submit/",
                      json={"lang": LANG, "question_id": str(question_id), "typed_code": code},
                      headers=headers, timeout=30)
        if r.status_code in (403, 429):
            time.sleep(6)
            continue
        break
    r.raise_for_status()
    sid = r.json()["submission_id"]
    for _ in range(20):
        time.sleep(2)
        res = http.get(f"{BASE}/submissions/detail/{sid}/check/", timeout=30).json()
        if res.get("state") == "SUCCESS":
            return res
    return {"status_msg": "Timeout waiting for result"}


def feedback(res):
    keys = ["status_msg", "last_testcase", "expected_output", "code_output",
            "full_runtime_error", "full_compile_error"]
    return "\n".join(f"{k}: {res[k]}" for k in keys if res.get(k))


def solve_one(is_first=True):
    q, difficulty = pick_question(is_first=is_first)
    slug = q["titleSlug"]
    d = gql(DETAIL_Q, {"titleSlug": slug})["question"]
    snippet = next((s["code"] for s in d["codeSnippets"] if s["langSlug"] == LANG), None)
    if not snippet:
        raise RuntimeError(f"No {LANG} template for {slug}")

    prompt = (f"Solve this LeetCode problem in {LANG}.\n\nTitle: {d['title']}\n\n"
              f"{strip_html(d['content'])}\n\nStarter code (keep exact class and method signature):\n{snippet}\n\n"
              f"Return ONLY the complete valid {LANG} code. Include any necessary standard library imports (e.g., java.util.* for Java). "
              "No markdown fences, no explanation, no comments. "
              "Use an optimal-complexity solution.")
    messages = [{"role": "user", "content": prompt}]
    code = ask_llm(messages)
    status = "not submitted"

    if AUTO_SUBMIT:
        for attempt in range(MAX_RETRIES + 1):
            res = submit_and_wait(slug, d["questionId"], code)
            status = res.get("status_msg", "Unknown")
            print(f"  attempt {attempt + 1}: {status}")
            if status == "Accepted" or attempt == MAX_RETRIES:
                break
            messages += [{"role": "assistant", "content": code},
                         {"role": "user", "content": "That failed:\n" + feedback(res) +
                          f"\nFix it. Return ONLY the complete corrected {LANG} code."}]
            code = ask_llm(messages)
            time.sleep(6)  # be gentle with LeetCode

    out = Path("solutions")
    out.mkdir(exist_ok=True)
    solution_file = out / f"{q['frontendQuestionId']}-{slug}.{EXT.get(LANG, 'java')}"
    solution_file.write_text(code, encoding="utf-8")
    new = not Path("log.csv").exists()
    with open("log.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "number", "title", "difficulty", "status"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), q["frontendQuestionId"],
                    d["title"], difficulty, status])
    print(f"{q['frontendQuestionId']}. {d['title']} [{difficulty}] -> {status}")
    print(f"  Saved solution to {solution_file}")
    return {
        "success": status == "Accepted",
        "number": q["frontendQuestionId"],
        "title": d["title"],
        "difficulty": difficulty,
        "status": status,
        "slug": slug,
        "error": None
    }


def send_daily_email(results):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("\n[Email Notification]")
        print(f"Recipient : {RECIPIENT_EMAIL}")
        print("Status    : Skipped (SMTP_EMAIL / SMTP_PASSWORD not set in .env)")
        print("To receive daily emails, generate a Gmail App Password and set SMTP_EMAIL and SMTP_PASSWORD.")
        return

    total_attempted = len(results)
    total_passed = sum(1 for r in results if r.get("success"))
    today_str = datetime.now().strftime("%Y-%m-%d")

    if total_passed == total_attempted and total_attempted > 0:
        subject = f"✅ LeetCode Daily Report - {total_passed} Problem(s) Solved ({today_str})"
    else:
        subject = f"⚠️ LeetCode Daily Report - {total_passed}/{total_attempted} Completed ({today_str})"

    # Plain text summary
    text_lines = [
        f"LeetCode Daily Automation Report - {today_str}",
        f"Account: harvish",
        f"Results: {total_passed}/{total_attempted} Accepted\n",
        "Problem Breakdown:",
        "-" * 50
    ]
    for r in results:
        sym = "✅" if r.get("success") else "❌"
        text_lines.append(f"{sym} #{r.get('number')}: {r.get('title')} [{r.get('difficulty')}] -> {r.get('status')}")
        if r.get("slug"):
            text_lines.append(f"   Link: https://leetcode.com/problems/{r.get('slug')}/")
        if r.get("error"):
            text_lines.append(f"   Error: {r.get('error')}")

    # HTML table
    rows_html = ""
    for r in results:
        badge_bg = "#28a745" if r.get("success") else "#dc3545"
        diff_color = {"EASY": "#00af9b", "MEDIUM": "#ffb800", "HARD": "#ff2d55"}.get(r.get("difficulty", "").upper(), "#6c757d")
        url = f"https://leetcode.com/problems/{r.get('slug')}/" if r.get("slug") else "#"
        err_div = f"<div style='color:#dc3545;font-size:12px;margin-top:4px;'>{html.escape(str(r.get('error')))}</div>" if r.get("error") else ""
        rows_html += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #eee;"><strong>#{r.get('number')}</strong></td>
            <td style="padding:10px;border-bottom:1px solid #eee;"><a href="{url}" style="color:#007bff;text-decoration:none;">{html.escape(r.get('title', 'Unknown'))}</a></td>
            <td style="padding:10px;border-bottom:1px solid #eee;"><span style="color:{diff_color};font-weight:bold;">{r.get('difficulty')}</span></td>
            <td style="padding:10px;border-bottom:1px solid #eee;"><span style="background:{badge_bg};color:#fff;padding:3px 8px;border-radius:4px;font-size:12px;">{r.get('status')}</span>{err_div}</td>
        </tr>
        """

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; margin:0; padding:20px; background-color:#f8f9fa;">
        <div style="max-width:620px; margin:auto; background:#ffffff; padding:24px; border-radius:8px; border:1px solid #e9ecef; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <h2 style="color:#2c3e50; margin-top:0;">LeetCode Daily Automation Report</h2>
            <p style="color:#6c757d; font-size:14px; margin-bottom:16px;">
                <strong>Date:</strong> {today_str} | <strong>Profile:</strong> <a href="https://leetcode.com/u/harvish/" style="color:#007bff;">harvish</a> | <strong>Status:</strong> {total_passed}/{total_attempted} Accepted
            </p>
            <table style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:14px;">
                <thead>
                    <tr style="background:#f1f3f5; text-align:left;">
                        <th style="padding:10px;">#</th>
                        <th style="padding:10px;">Title</th>
                        <th style="padding:10px;">Difficulty</th>
                        <th style="padding:10px;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            <p style="font-size:13px; color:#6c757d;">
                Keep your daily streak alive! View your stats on <a href="https://leetcode.com/u/harvish/" style="color:#007bff;">LeetCode Profile</a>.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"LeetCode Daily Bot <{SMTP_EMAIL}>"
    msg["To"] = RECIPIENT_EMAIL

    msg.attach(MIMEText("\n".join(text_lines), "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        print(f"-> Daily email report successfully sent to {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"-> Failed to send email to {RECIPIENT_EMAIL}: {e}")


if __name__ == "__main__":
    count = random.choice([1, 2])
    print(f"Starting daily run: solving {count} question(s)...")
    results = []
    for i in range(count):
        try:
            res = solve_one(is_first=(i == 0))
            if res:
                results.append(res)
        except Exception as e:
            print("Error:", e)
            results.append({
                "success": False,
                "number": "?",
                "title": "Problem Error",
                "difficulty": "?",
                "status": "Failed",
                "slug": "",
                "error": str(e)
            })
        if i < count - 1:
            time.sleep(6)

    send_daily_email(results)
