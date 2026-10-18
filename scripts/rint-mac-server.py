#!/usr/bin/env python3
"""Private Mac hosting, separate from the local demo."""
# Trusted, fixed local subprocesses and intentional command-line status output.
# ruff: noqa: S603, T201

import argparse
import json
import os
import plistlib
import secrets
import signal
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".local/personal"
CONFIG = DATA / "environment.json"
LABEL = "org.rint.personal-server"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
PYTHON = ROOT / ".venv/bin/python"


def call(args, **kwargs):
    return subprocess.run(
        [str(a) for a in args], cwd=ROOT, check=True, **kwargs
    )


def environment():
    return {**os.environ, **json.loads(CONFIG.read_text())}


def services():
    pg = (
        Path(
            call(
                ["/opt/homebrew/bin/brew", "--prefix", "postgresql@17"],
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        / "bin"
    )
    database = ROOT / ".local/postgres"
    if not (database / "PG_VERSION").exists():
        raise SystemExit(
            "Initialize local PostgreSQL with rint-dev-services.sh first."
        )
    ready = (
        subprocess.run(
            [str(pg / "pg_isready"), "-h", "127.0.0.1", "-p", "55432"],
            stdout=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if not ready:
        call(
            [
                pg / "pg_ctl",
                "-D",
                database,
                "-l",
                ROOT / ".local/postgres.log",
                "-o",
                "-h 127.0.0.1 -p 55432 -k /private/tmp",
                "start",
            ]
        )
    redis_cli = "/opt/homebrew/bin/redis-cli"
    if subprocess.run(
        [redis_cli, "-p", "56379", "ping"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode:
        call(
            [
                "/opt/homebrew/bin/redis-server",
                "--bind",
                "127.0.0.1",
                "--port",
                "56379",
                "--daemonize",
                "yes",
                "--dir",
                ROOT / ".local",
                "--pidfile",
                ROOT / ".local/redis.pid",
                "--logfile",
                ROOT / ".local/redis.log",
            ]
        )
    return pg


def prepare(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise SystemExit(
            "Provide an HTTPS origin, without credentials, path or query."
        )
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    DATA.chmod(0o700)
    if CONFIG.exists():
        config = json.loads(CONFIG.read_text())
        if config["UI_URL"] != url.rstrip("/"):
            raise SystemExit(
                "Existing URL differs; edit the private environment "
                "file deliberately."
            )
    else:
        config = {
            "APP_SETTINGS": "fittrackee.config.ProductionConfig",
            "APP_SECRET_KEY": secrets.token_hex(32),
            "UI_URL": url.rstrip("/"),
            "DATABASE_URL": "postgresql://localhost:55432/rint_personal",
            "REDIS_URL": "redis://127.0.0.1:56379/1",
            "UPLOAD_FOLDER": str(DATA),
            "STATICMAP_CACHE_DIR": str(DATA / "maps"),
            "EMAIL_URL": "",
            "SENDER_EMAIL": "",
            "API_RATE_LIMITS": "300 per 5 minutes",
            "FLASK_DEBUG": "0",
        }
        with CONFIG.open("x") as target:
            CONFIG.chmod(0o600)
            json.dump(config, target, indent=2)
    pg = services()
    exists = call(
        [
            pg / "psql",
            "-h",
            "127.0.0.1",
            "-p",
            "55432",
            "postgres",
            "-tAc",
            "SELECT 1 FROM pg_database WHERE datname='rint_personal'",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not exists:
        call(
            [
                pg / "createdb",
                "-h",
                "127.0.0.1",
                "-p",
                "55432",
                "rint_personal",
            ]
        )
        call(
            [
                pg / "psql",
                "-h",
                "127.0.0.1",
                "-p",
                "55432",
                "rint_personal",
                "-c",
                "CREATE EXTENSION IF NOT EXISTS postgis",
            ]
        )
    call([ROOT / ".venv/bin/ftcli", "db", "upgrade"], env=environment())
    # The first real account can register. Later registrations need the owner
    # to deliberately raise the limit. Never alter existing account settings.
    call(
        [
            PYTHON,
            "-c",
            "from fittrackee import create_app, db; "
            "from fittrackee.application.models import AppConfig; "
            "from fittrackee.users.models import User; app=create_app(); "
            "ctx=app.app_context(); ctx.push(); c=AppConfig.query.first(); "
            "c.max_users = 1 if User.query.count() == 0 else c.max_users; "
            "c.max_single_file_size=max(c.max_single_file_size, 33554432); "
            "c.max_zip_file_size=max(c.max_zip_file_size, 536870912); "
            "db.session.commit()",
        ],
        env=environment(),
    )
    print(f"Prepared private personal server: {config['UI_URL']}")


def run():
    services()
    env = environment()
    commands = [
        [
            ROOT / ".venv/bin/gunicorn",
            "fittrackee:create_app()",
            "--bind",
            "127.0.0.1:5081",
            "--workers",
            "2",
            "--timeout",
            "180",
            "--error-logfile",
            "-",
            "--no-control-socket",
        ],
        [
            ROOT / ".venv/bin/dramatiq",
            "fittrackee.tasks:broker",
            "--processes",
            "1",
            "--threads",
            "4",
        ],
    ]
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for command in commands:
            children.append(
                subprocess.Popen(
                    [str(a) for a in command],
                    cwd=ROOT,
                    env=env,
                    start_new_session=True,
                )
            )
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise RuntimeError(
                    "A server process exited; launchd will restart it."
                )
            time.sleep(1)
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        for child in children:
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()


def install():
    environment()  # Fail before registering anything if setup is incomplete.
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    job = {
        "Label": LABEL,
        "ProgramArguments": [
            str(PYTHON),
            str(Path(__file__).resolve()),
            "run",
        ],
        "WorkingDirectory": str(ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 15,
        "ExitTimeOut": 75,
        "Umask": 0o077,
        "EnvironmentVariables": {
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "PYTHONUNBUFFERED": "1",
        },
        "StandardOutPath": str(DATA / "server.log"),
        "StandardErrorPath": str(DATA / "server.log"),
    }
    if PLIST.exists() and plistlib.loads(PLIST.read_bytes()) != job:
        raise SystemExit(
            "An existing launch agent differs; inspect it before replacing it."
        )
    PLIST.write_bytes(plistlib.dumps(job))
    PLIST.chmod(0o600)
    target = f"gui/{os.getuid()}"
    loaded = (
        subprocess.run(
            ["/bin/launchctl", "print", f"{target}/{LABEL}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if not loaded:
        call(["/bin/launchctl", "bootstrap", target, PLIST])
    print("Personal server installed; starts when you log in to this Mac.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare").add_argument("--url", required=True)
    sub.add_parser("run")
    sub.add_parser("install")
    sub.add_parser("cli").add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.umask(0o077)
    if args.command == "prepare":
        prepare(args.url)
    elif args.command == "install":
        install()
    elif args.command == "cli":
        call([ROOT / ".venv/bin/ftcli", *args.arguments], env=environment())
    else:
        run()
