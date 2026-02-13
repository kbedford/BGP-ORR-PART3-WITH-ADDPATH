#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
from pathlib import Path

def run(cmd, cwd=None):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)

def get_global(key):
    p = subprocess.run(["git", "config", "--global", "--get", key],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""

def ensure_identity(name, email):
    if not get_global("user.name"):
        if not name:
            raise SystemExit("Missing git user.name. Pass --git-name once.")
        run(["git", "config", "--global", "user.name", name])
    if not get_global("user.email"):
        if not email:
            raise SystemExit("Missing git user.email. Pass --git-email once.")
        run(["git", "config", "--global", "user.email", email])

def repo_has_changes(path):
    p = subprocess.run(["git", "status", "--porcelain"], cwd=path,
                       capture_output=True, text=True, check=True)
    return bool(p.stdout.strip())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("repo", help="GitHub repo name, e.g. BGP-ORR-PART3-WITH-ADDPATH")
    p.add_argument("--user", default="kbedford", help="GitHub username")
    p.add_argument("--source", default=os.getcwd(),
                   help="Source directory to copy when creating a new repo")
    p.add_argument("--dest-root", default=str(Path.home()),
                   help="Where repos live (default: ~)")
    p.add_argument("--git-name", default="")
    p.add_argument("--git-email", default="")
    p.add_argument("--message", default="Update lab")
    args = p.parse_args()

    ensure_identity(args.git_name, args.git_email)

    dest = Path(args.dest_root) / args.repo
    source = Path(args.source)

    if dest.exists() and (dest / ".git").exists():
        # Update existing repo
        if repo_has_changes(dest):
            run(["git", "add", "."], cwd=dest)
            run(["git", "commit", "-m", args.message], cwd=dest)
        run(["git", "push", "-u", "origin", "main"], cwd=dest)
        print(f"Updated existing repo at {dest}")
        return

    # Create new repo by copying source
    if dest.exists():
        raise SystemExit(f"Destination exists but is not a git repo: {dest}")

    shutil.copytree(source, dest)
    if (dest / ".git").exists():
        shutil.rmtree(dest / ".git")

    run(["git", "init"], cwd=dest)
    run(["git", "add", "."], cwd=dest)
    run(["git", "commit", "-m", "Initial ORR lab"], cwd=dest)
    run(["git", "branch", "-m", "main"], cwd=dest)
    run(["git", "remote", "add", "origin",
         f"git@github.com:{args.user}/{args.repo}.git"], cwd=dest)
    run(["git", "push", "-u", "origin", "main"], cwd=dest)
    print(f"Created new repo at {dest}")

if __name__ == "__main__":
    main()

