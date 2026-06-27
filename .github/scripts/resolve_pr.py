#!/usr/bin/env python3
# NOTE: AI slop - generated, unreviewed.
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
FILE = "development-updates.md"
MERGE_SCRIPT = "/tmp/dev_updates.py"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "dev-updates-mergeable",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def run(cmd, check=True, capture=False):
    print("+ " + " ".join(cmd), flush=True)
    res = subprocess.run(cmd, check=check, text=True, capture_output=capture)
    return res.stdout.strip() if capture else ""


def git_show(ref_path):
    res = subprocess.run(["git", "show", ref_path], text=True, capture_output=True)
    return res.stdout if res.returncode == 0 else ""


def fail(msg):
    print(f"::error::{msg}")
    return 1


def main(pr_number):
    pr = api(f"/repos/{REPO}/pulls/{pr_number}")
    if pr.get("state") != "open":
        print(f"PR #{pr_number} not open; nothing to do.")
        return 0

    head_repo = pr["head"]["repo"]["full_name"]
    head_branch = pr["head"]["ref"]
    base_branch = pr["base"]["ref"]
    maintainer_can_modify = pr.get("maintainer_can_modify", False)
    owner = REPO.split("/")[0]
    same_repo = head_repo.split("/")[0] == owner

    files = api(f"/repos/{REPO}/pulls/{pr_number}/files")
    if not any(f["filename"] == FILE for f in files):
        print(f"PR #{pr_number} does not touch {FILE}; nothing to do.")
        return 0

    auth_remote = f"https://x-access-token:{TOKEN}@github.com/{head_repo}.git"

    run(["git", "fetch", "origin", base_branch], check=True)
    subprocess.run(["git", "remote", "remove", "prhead"],
                   capture_output=True, text=True)  # ignore if absent
    run(["git", "remote", "add", "prhead", auth_remote], check=True)
    # Fetch the branch tip into a stable local ref so git show always resolves.
    run(["git", "fetch", "prhead", f"{head_branch}:_prhead"], check=True)

    head_ref = "_prhead"
    main_ref = f"origin/{base_branch}"
    merge_base = run(["git", "merge-base", head_ref, main_ref], capture=True)
    print(f"merge-base = {merge_base}")

    base_content = git_show(f"{merge_base}:{FILE}")
    ours_content = git_show(f"{head_ref}:{FILE}")
    theirs_content = git_show(f"{main_ref}:{FILE}")

    with tempfile.TemporaryDirectory() as d:
        bp, op, tp, mp = (os.path.join(d, n) for n in ("base", "ours", "theirs", "merged"))
        open(bp, "w").write(base_content)
        open(op, "w").write(ours_content)
        open(tp, "w").write(theirs_content)
        res = subprocess.run(
            [sys.executable, MERGE_SCRIPT, "merge", bp, op, tp, "--output", mp],
            text=True, capture_output=True,
        )
        print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        merged = open(mp).read()

    if res.returncode != 0 or "<!-- CONFLICT" in merged:
        return fail(
            "Two changes target the same cell in development-updates.md. "
            "Resolve manually (look for '<!-- CONFLICT' markers)."
        )

    if not maintainer_can_modify and not same_repo:
        return fail(
            "This PR conflicts with development-updates.md and 'Allow edits by "
            "maintainers' is off, so the branch can't be synced automatically. "
            "Enable it and re-run this check, or run "
            "`python3 scripts/dev_updates.py format development-updates.md` locally."
        )

    # Already in sync? If the base tip is an ancestor of the PR head and the
    # table already equals the merge result, there is nothing to do.
    base_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", main_ref, head_ref]
    ).returncode == 0
    if base_is_ancestor and merged == ours_content:
        print(f"PR #{pr_number}: already in sync with {base_branch}; mergeable.")
        return 0

    # Do a real git merge of the base branch into the PR branch. Git merges every
    # file normally (so files added on the base branch -- e.g. workflows -- are
    # left exactly as they are and never appear in our commit's diff), and we only
    # step in to resolve development-updates.md with the semantic merge. The result
    # is a proper merge commit, so merging the PR back into the base is clean.
    run(["git", "checkout", "-q", "-B", "_autofix", head_ref], check=True)
    merge_rc = subprocess.run(
        ["git", "merge", "--no-commit", "--no-ff", main_ref],
        text=True, capture_output=True,
    )
    print(merge_rc.stdout)
    if merge_rc.stderr:
        print(merge_rc.stderr, file=sys.stderr)

    # Any conflict outside the table means a real, non-table change clashes ->
    # leave it for a human.
    conflicted = run(["git", "diff", "--name-only", "--diff-filter=U"], capture=True).split()
    others = [f for f in conflicted if f != FILE]
    if others:
        run(["git", "merge", "--abort"], check=False)
        return fail(
            "Merge conflicts outside development-updates.md ("
            + ", ".join(others) + "); not auto-syncing."
        )

    # Write the semantic merge of the table over whatever git produced and stage.
    with open(FILE, "w") as fh:
        fh.write(merged)
    run(["git", "add", FILE], check=True)

    run(["git", "commit", "--no-edit",
         "-m", "Merge base branch into PR and sync development-updates.md"], check=True)
    run(["git", "push", "prhead", f"_autofix:{head_branch}"], check=True)
    print(f"PR #{pr_number}: synced and pushed to {head_repo}:{head_branch}.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: resolve_pr.py <pr_number>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(int(sys.argv[1])))
