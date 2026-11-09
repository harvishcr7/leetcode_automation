"""
LeetCode Fast Batch Solver
Solves non-paid, unsolved problems until the target solved count is reached.
"""
import csv
import html
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE = "https://leetcode.com"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "")
LEETCODE_CSRF = os.getenv("LEETCODE_CSRF", "")
LANG = os.getenv("LANG", "java")
EXT = {"java": "java", "python3": "py", "cpp": "cpp"}

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY is missing in .env")
    sys.exit(1)
if not LEETCODE_SESSION or not LEETCODE_CSRF:
    print("Error: LEETCODE_SESSION or LEETCODE_CSRF is missing in .env")
    sys.exit(1)

http = requests.Session()
http.headers.update({
    "Cookie": f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={LEETCODE_CSRF}",
    "x-csrftoken": LEETCODE_CSRF,
    "Content-Type": "application/json",
    "Referer": BASE + "/problemset/",
    "Origin": BASE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
})


def gql(query, variables=None):
    for attempt in range(3):
        try:
            r = http.post(f"{BASE}/graphql", json={"query": query, "variables": variables or {}}, timeout=30)
            r.raise_for_status()
            res = r.json()
            if "errors" in res and not res.get("data"):
                raise RuntimeError(str(res["errors"]))
            return res.get("data", {})
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def get_current_stats():
    # Get username
    user_status = gql("{ userStatus { isSignedIn username } }").get("userStatus", {})
    if not user_status.get("isSignedIn"):
        raise RuntimeError("LeetCode session cookie expired or invalid. Please refresh LEETCODE_SESSION.")
    username = user_status.get("username")

    # Get solved count
    q = """query userProblemsSolved($username: String!) {
      matchedUser(username: $username) {
        submitStatsGlobal {
          acSubmissionNum { difficulty count }
        }
      }
    }"""
    stats_data = gql(q, {"username": username})
    stats = stats_data.get("matchedUser", {}).get("submitStatsGlobal", {}).get("acSubmissionNum", [])
    total_solved = 0
    for s in stats:
        if s.get("difficulty") == "All":
            total_solved = s.get("count", 0)
    return username, total_solved


def get_candidate_questions(limit=150):
    """Fetch pool of unsolved, non-paid Easy & Medium questions."""
    list_q = """query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
        questions: data { frontendQuestionId: questionFrontendId title titleSlug difficulty status paidOnly: isPaidOnly }
      }
    }"""

    candidates = []
    # Fetch mostly Easy for maximum speed and 100% acceptance rate, followed by Medium
    for diff in ["EASY", "MEDIUM"]:
        for skip in (0, 50, 100, 150):
            data = gql(list_q, {
                "categorySlug": "", "skip": skip, "limit": 50,
                "filters": {"difficulty": diff, "status": "NOT_STARTED"}
            })
            qs = data.get("problemsetQuestionList", {}).get("questions", [])
            for q in qs:
                if not q.get("paidOnly") and q.get("status") != "ac":
                    candidates.append(q)
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in candidates:
        if q["frontendQuestionId"] not in seen:
            seen.add(q["frontendQuestionId"])
            unique.append(q)
    return unique


DETAIL_Q = """query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) { questionId title content codeSnippets { langSlug code } }
}"""


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
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-3.8-flash"
    ]
    models_to_try = list(dict.fromkeys(models_to_try))

    last_error = None
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(url, json={"contents": contents}, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    return clean_code(text)
            elif resp.status_code in (404, 429, 500, 503):
                last_error = f"{resp.status_code} on {model_name}"
                time.sleep(1)
                continue
            else:
                resp.raise_for_status()
        except requests.RequestException as e:
            last_error = str(e)
            time.sleep(1)
            continue
    raise RuntimeError(f"Gemini API error: {last_error}")


def submit_and_wait(slug, question_id, code):
    url = f"{BASE}/problems/{slug}/submit/"
    headers = {"Referer": f"{BASE}/problems/{slug}/", "Origin": BASE}
    r = None
    for attempt in range(3):
        r = http.post(url, json={"lang": LANG, "question_id": str(question_id), "typed_code": code}, headers=headers, timeout=30)
        if r.status_code in (403, 429):
            time.sleep(6)
            continue
        break
    r.raise_for_status()
    data = r.json()
    if "submission_id" not in data:
        return {"status_msg": str(data)}
    sid = data["submission_id"]

    for _ in range(15):
        time.sleep(2)
        res = http.get(f"{BASE}/submissions/detail/{sid}/check/", timeout=30).json()
        if res.get("state") == "SUCCESS":
            return res
    return {"status_msg": "Timeout waiting for result"}


def solve_question(q):
    slug = q["titleSlug"]
    q_data = gql(DETAIL_Q, {"titleSlug": slug}).get("question")
    if not q_data:
        return False, "Failed to fetch question details"

    snippets = q_data.get("codeSnippets", [])
    snippet = next((s["code"] for s in snippets if s["langSlug"] == LANG), None)
    if not snippet:
        return False, f"No {LANG} template found"

    desc = html.unescape(re.sub(r"<[^>]+>", "", q_data.get("content", "") or ""))
    prompt = (
        f"Solve this LeetCode problem in {LANG}.\n\n"
        f"Title: {q_data['title']}\n\n{desc}\n\n"
        f"Starter code (keep exact class and method signature):\n{snippet}\n\n"
        "Return ONLY the complete valid Python code. No markdown fences, no explanation, no comments. "
        "Use optimal time and space complexity."
    )
    messages = [{"role": "user", "content": prompt}]
    code = ask_gemini(messages)

    res = submit_and_wait(slug, q_data["questionId"], code)
    status = res.get("status_msg", "Unknown")

    # If first attempt fails, do 1 quick retry with feedback
    if status != "Accepted":
        keys = ["status_msg", "last_testcase", "expected_output", "code_output", "full_runtime_error", "full_compile_error"]
        feedback = "\n".join(f"{k}: {res[k]}" for k in keys if res.get(k))
        messages += [
            {"role": "assistant", "content": code},
            {"role": "user", "content": f"That failed with:\n{feedback}\nFix it. Return ONLY the complete corrected Python code."}
        ]
        time.sleep(3)
        code = ask_gemini(messages)
        res = submit_and_wait(slug, q_data["questionId"], code)
        status = res.get("status_msg", "Unknown")

    if status == "Accepted":
        # Save solution
        out = Path("solutions")
        out.mkdir(exist_ok=True)
        sol_file = out / f"{q['frontendQuestionId']}-{slug}.{EXT.get(LANG, 'py')}"
        sol_file.write_text(code, encoding="utf-8")

        # Log
        new_log = not Path("log.csv").exists()
        with open("log.csv", "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_log:
                w.writerow(["date", "number", "title", "difficulty", "status"])
            w.writerow([datetime.now().isoformat(timespec="seconds"), q["frontendQuestionId"], q_data["title"], q["difficulty"], status])

        return True, status
    return False, status


def main():
    target = 400
    if len(sys.argv) > 1:
        try:
            target = int(sys.argv[1])
        except ValueError:
            pass

    username, current_solved = get_current_stats()
    print("=" * 60)
    print(f"LeetCode Fast Batch Solver for: {username}")
    print(f"Current Solved Count: {current_solved}")
    print(f"Target Solved Count : {target}")
    needed = max(0, target - current_solved)
    print(f"Problems Needed     : {needed}")
    print("=" * 60)

    if needed <= 0:
        print("Target already achieved! Nothing to do.")
        return

    solved_this_session = 0
    while current_solved + solved_this_session < target:
        questions = get_candidate_questions(limit=100)
        if not questions:
            print("No more candidate questions available.")
            break

        print(f"\nFetched {len(questions)} candidate questions. Starting solving loop...\n")

        for q in questions:
            if current_solved + solved_this_session >= target:
                break

            qid = q["frontendQuestionId"]
            title = q["title"]
            diff = q["difficulty"]

            print(f"[{current_solved + solved_this_session + 1}/{target}] Solving #{qid}: {title} ({diff})...", end=" ", flush=True)

            try:
                success, status = solve_question(q)
                if success:
                    solved_this_session += 1
                    total_now = current_solved + solved_this_session
                    print(f"-> ACCEPTED! (Total: {total_now}/{target})")
                else:
                    print(f"-> {status} (skipping to keep pace)")
            except Exception as e:
                print(f"-> Error: {e}")

            # Safe cooldown to prevent LeetCode rate limit
            time.sleep(5)

        # Refresh stats from LeetCode
        try:
            _, current_solved = get_current_stats()
            solved_this_session = 0
            print(f"\n-- LeetCode Verified Solved Count: {current_solved}/{target} --\n")
        except Exception:
            pass

    print("=" * 60)
    print(f"FINISHED! Total solved: {current_solved + solved_this_session}/{target}")
    print("=" * 60)


if __name__ == "__main__":
    main()
