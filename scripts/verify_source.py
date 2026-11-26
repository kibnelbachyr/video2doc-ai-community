"""Selected source checks; not a comprehensive secret or vulnerability scan."""
import ast
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bAccountKey=[A-Za-z0-9+/]{80,}={0,2}"),
)


def main():
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    findings = []
    count = 0
    for name in filter(None, paths):
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            findings.append((name, "not a regular file"))
            continue
        count += 1
        if path.name == ".env" or path.suffix in {".pem", ".pfx", ".key"}:
            findings.append((name, "sensitive path"))
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append((name, "unexpected binary"))
            continue
        if path.suffix == ".py":
            try:
                ast.parse(source, filename=name)
            except SyntaxError:
                findings.append((name, "Python syntax"))
        if any(pattern.search(source) for pattern in PATTERNS):
            findings.append((name, "selected credential pattern"))
    for name, reason in findings:
        print(f"{name}: {reason}")
    print(f"Tracked files checked: {count}; findings: {len(findings)}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
