from __future__ import annotations

# SPDX-License-Identifier: GPL-3.0-only
# # Modified & Extended by xboyrex (Mayank Droid) — XBOYREX Edition v8.1
# Repository: https://github.com/xboyrex/miunlocktool
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

import argparse
import base64
import getpass
import hashlib
import json
import os
import random
import socket
import struct
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
import urllib.request

import requests

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    _HAS_RICH = True
    console = Console(highlight=False)
except ImportError:
    _HAS_RICH = False
    console = None

# Enable ANSI escape sequences and UTF-8 on Windows terminal
if sys.platform == "win32":
    os.system("")
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VERSION = "8.1"
REPO_URL = "https://github.com/xboyrex/miunlocktool"
WEB_URL = "https://xboyrex.github.io/mayank-droid/"
TG_URL = "https://t.me/MayankDroid7"

API_HOST = "sgp-api.buy.mi.com"
STATUS_URL = f"https://{API_HOST}/bbs/api/global/user/bl-switch/state"
APPLY_URL = f"https://{API_HOST}/bbs/api/global/apply/bl-auth"
PING_HOSTS = ["sgp-api.buy.mi.com", "api.buy.mi.com", "account.xiaomi.com"]
NTP_SERVERS = [
    "time1.google.com", "time2.google.com", "time3.google.com",
    "time4.google.com", "time.android.com", "time.aws.com",
    "time.google.com", "time.cloudflare.com", "ntp.time.in.ua",
    "stratum1.net", "ntp5.stratum2.ru",
]

# Standalone CLI config location
CLI_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "xiaomi-unlock-tool"
CLI_CONFIG_FILE = CLI_CONFIG_DIR / "config.json"

# Desktop 8.1 config location (for cross-compatibility)
if os.name == "nt":
    DESKTOP_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "XboyrexUnlockStudio"
else:
    DESKTOP_CONFIG_DIR = Path.home() / ".config" / "XboyrexUnlockStudio"
DESKTOP_CONFIG_FILE = DESKTOP_CONFIG_DIR / "config.json"

BIG_XBOYREX_LOGO = (
    "██╗  ██╗██████╗  ██████╗ ██╗   ██╗██████╗ ███████╗██╗  ██╗\n"
    "╚██╗██╔╝██╔══██╗██╔═══██╗╚██╗ ██╔╝██╔══██╗██╔════╝╚██╗██╔╝\n"
    " ╚███╔╝ ██████╔╝██║   ██║ ╚████╔╝ ██████╔╝█████╗   ╚███╔╝ \n"
    " ██╔██╗ ██╔══██╗██║   ██║  ╚██╔╝  ██╔══██╗██╔══╝   ██╔██╗ \n"
    "██╔╝ ██╗██████╔╝╚██████╔╝   ██║   ██║  ██║███████╗██╔╝ ██╗\n"
    "╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝"
)

# ==============================================================================
# Smart DoH DNS Shield (Cloudflare 1.1.1.1 + Google 8.8.8.8)
# ==============================================================================
_DNS_CACHE: dict[str, str] = {}
DOH_ENDPOINTS = (
    ("Cloudflare 1.1.1.1", "https://1.1.1.1/dns-query?name={host}&type=A"),
    ("Google 8.8.8.8", "https://8.8.8.8/resolve?name={host}&type=A"),
)


def resolve_host_smart(host: str, timeout: float = 2.0) -> str:
    if host in _DNS_CACHE:
        return _DNS_CACHE[host]
    try:
        ip = socket.gethostbyname(host)
        if ip and not ip.startswith("127.") and ip != "0.0.0.0":
            _DNS_CACHE[host] = ip
            return ip
    except Exception:
        pass
    for _, tmpl in DOH_ENDPOINTS:
        try:
            req = urllib.request.Request(tmpl.format(host=host), headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for ans in data.get("Answer", []):
                    if ans.get("type") == 1 and ans.get("data"):
                        ip = ans["data"]
                        _DNS_CACHE[host] = ip
                        return ip
        except Exception:
            continue
    return ""


def install_smart_dns_hook() -> None:
    orig_getaddrinfo = socket.getaddrinfo

    def _smart_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            return orig_getaddrinfo(host, port, family, type, proto, flags)
        except socket.gaierror:
            if isinstance(host, str):
                ip = resolve_host_smart(host)
                if ip:
                    return orig_getaddrinfo(ip, port, family, type, proto, flags)
            raise

    if getattr(socket.getaddrinfo, "__name__", "") != "_smart_getaddrinfo":
        socket.getaddrinfo = _smart_getaddrinfo


install_smart_dns_hook()


def detect_language() -> str:
    lang = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    lang = lang.lower()
    return "ru" if lang.startswith("ru") else "en"


TEXT = {
    "ru": {
        "title": "Xiaomi Unlock Tool 8.1 · XBOYREX Edition",
        "tab_settings": "Настройки и Авторизация (Token / QR)",
        "tab_submit": "Подача заявки (Sub-ms NTP Engine)",
        "tab_miunlock": "Mi Unlock (Fastboot Unlocker)",
        "back": "Назад",
        "select_tab": "Выберите пункт [01-03 / Q]: ",
        "settings_token": "ServiceToken",
        "settings_language": "Язык",
        "settings_check": "Проверка статуса перед заявкой",
        "settings_config": "Файл конфигурации",
        "settings_desktop_config": "Конфиг Desktop 8.1",
        "settings_ping": "Проверить соединение с Xiaomi API",
        "settings_set_token": "Ввести New_bbs_ServiceToken вручную",
        "settings_qr_login": "Авто-вход через Браузер / QR-код (Xiaomi Account)",
        "settings_session_login": "Извлечь токен из сохранённой сессии (~/.migatesession)",
        "settings_toggle_check": "Переключить проверку статуса",
        "submit_run": "Подать заявку (Авторежим #2 + Dynamic RTT)",
        "submit_status": "Проверить статус аккаунта",
        "submit_ping": "Ping Xiaomi API & NTP",
        "mi_install_run": "Установить / запустить Mi Unlock",
        "mi_status": "Проверить установку Mi Unlock",
        "mi_note": "Mi Unlock запускается через пакет Python `miunlock`.",
        "mi_python": "Python",
        "mi_package": "Пакет miunlock",
        "installed": "установлен",
        "not_installed": "не установлен",
        "python_not_found": "Python не найден.",
        "mi_installing": "Устанавливаю пакет miunlock...",
        "mi_install_failed": "Не удалось установить пакет miunlock.",
        "mi_launching": "Запускаю Mi Unlock...",
        "mi_launch_failed": "Не удалось запустить Mi Unlock: {error}",
        "menu_exit": "Выход",
        "choose": "Выберите: ",
        "token_prompt": "New_bbs_ServiceToken: ",
        "token_empty": "Cookie/token не указан.",
        "checking": "Проверка токена и статуса аккаунта...",
        "cookie_bad": "Cookie устарел или недействителен (100004).",
        "ready": "Аккаунт готов к подаче заявки.",
        "blocked": "Аккаунт заблокирован до: {value}",
        "not_ready": "Аккаунт ещё не готов (менее 30 дней в Mi Community).",
        "approved": "Аккаунт уже одобрен! Дата: {value}",
        "unknown_status": "Неизвестный статус. code={code}, data={data}",
        "wait": "Ожидание 23:59:59 по Пекину ({seconds:.1f} сек.)...",
        "reached": "Время 23:59:59 по Пекину достигнуто. Отправка пакета запросов (Авторежим #2)...",
        "interrupted": "Процесс прерван пользователем.",
        "saved": "ServiceToken успешно сохранён!",
        "not_saved": "Пустой токен не сохранён.",
        "status_fail": "Проверка статуса не пройдена. Заявка не отправлена.",
        "skip": "Проверка статуса отключена.",
        "done": "Завершено. Успешных ответов: {success}/{total}",
        "apply": "{label}: заявка одобрена! (код: {code})",
        "not_submitted": "{label}: заявка не отправлена. Повторить можно: {value}",
        "maybe_approved": "{label}: сервер сообщает, что заявка, возможно, одобрена (100003).",
        "rejected": "{label}: запрос отклонён сервером (100001 - лимит квоты исчерпан).",
        "unknown_response": "{label}: ответ: {result}",
        "bad_json": "Сервер вернул некорректный JSON.",
        "bad_json_label": "{label}: сервер вернул некорректный JSON.",
        "request_error": "Ошибка запроса: {error}",
        "ntp": "NTP синхронизация: {server}",
        "beijing": "Время Пекина: {value} (UTC+8)",
        "ntp_fail": "Не удалось подключиться ни к одному NTP-серверу.",
        "ping_title": "Xiaomi API & Gateway Ping",
        "unknown_choice": "Неизвестный пункт.",
        "status_off": "Проверка статуса перед заявкой: OFF",
        "status_on": "Проверка статуса перед заявкой: ON",
        "config_error": "Не удалось загрузить конфигурацию: {error}",
        "save_error": "Не удалось сохранить конфигурацию: {error}",
        "device": "{label}: device_id={device_id}",
        "response": "{label}: code={code} | {message}",
        "found_saved_session": "Обнаружена сохранённая сессия Mi Account ({source}, ID: {uid}).",
    },
    "en": {
        "title": "Xiaomi Unlock Tool 8.1 · XBOYREX Edition",
        "tab_settings": "Settings & Auth (Token / QR / Session)",
        "tab_submit": "Submit Quota Application (Sub-ms NTP Engine)",
        "tab_miunlock": "Mi Unlock (Fastboot Bootloader Unlocker)",
        "back": "Back",
        "select_tab": "Select Operation [01-03 / Q]: ",
        "settings_token": "ServiceToken",
        "settings_language": "Language",
        "settings_check": "Status check before application",
        "settings_config": "Configuration file",
        "settings_desktop_config": "Desktop 8.1 Config",
        "settings_ping": "Test connection & latency to Xiaomi API",
        "settings_set_token": "Enter New_bbs_ServiceToken manually",
        "settings_qr_login": "Auto Login via Browser / QR URL (Xiaomi Account)",
        "settings_session_login": "Extract token from saved session (~/.migatesession)",
        "settings_toggle_check": "Toggle status check before submit",
        "submit_run": "Submit application (Auto Mode #2 + Dynamic RTT)",
        "submit_status": "Check account eligibility status",
        "submit_ping": "Ping Xiaomi API & Stratum-1 NTP",
        "mi_install_run": "Install / launch Mi Unlock (Fastboot)",
        "mi_status": "Check Mi Unlock installation",
        "mi_note": "Mi Unlock is launched through the Python `miunlock` package.",
        "mi_python": "Python",
        "mi_package": "miunlock package",
        "installed": "installed",
        "not_installed": "not installed",
        "python_not_found": "Python was not found.",
        "mi_installing": "Installing the miunlock package...",
        "mi_install_failed": "Could not install the miunlock package.",
        "mi_launching": "Launching Mi Unlock...",
        "mi_launch_failed": "Could not launch Mi Unlock: {error}",
        "menu_exit": "Quit",
        "choose": "Choice › ",
        "token_prompt": "New_bbs_ServiceToken: ",
        "token_empty": "Cookie/token is not specified.",
        "checking": "Checking token and account status...",
        "cookie_bad": "Cookie is expired or invalid (100004).",
        "ready": "Account is READY to submit the unlock application!",
        "blocked": "Account is blocked until: {value}",
        "not_ready": "Account is not ready yet (under 30 days registered in Mi Community).",
        "approved": "Account is ALREADY APPROVED! Date: {value}",
        "unknown_status": "Unknown status. code={code}, data={data}",
        "wait": "Waiting for 23:59:59 Beijing time ({seconds:.1f} sec.)...",
        "reached": "23:59:59 Beijing time reached. Firing sub-ms scheduled requests (Auto Mode #2)...",
        "interrupted": "Process interrupted by user.",
        "saved": "ServiceToken saved successfully!",
        "not_saved": "Empty token was not saved.",
        "status_fail": "Status check failed. Application was not sent.",
        "skip": "Status check disabled.",
        "done": "Finished. Successful responses: {success}/{total}",
        "apply": "{label}: APPLICATION APPROVED! (code: {code})",
        "not_submitted": "{label}: application was not submitted. Retry after: {value}",
        "maybe_approved": "{label}: server reports that the application may be approved (100003).",
        "rejected": "{label}: request rejected (100001 - daily quota exceeded).",
        "unknown_response": "{label}: unknown response: {result}",
        "bad_json": "Server returned invalid JSON.",
        "bad_json_label": "{label}: server returned invalid JSON.",
        "request_error": "Request error: {error}",
        "ntp": "NTP Sync: {server}",
        "beijing": "Beijing time: {value} (UTC+8)",
        "ntp_fail": "Could not connect to any NTP server.",
        "ping_title": "Xiaomi API & Gateway Ping",
        "unknown_choice": "Unknown option.",
        "status_off": "Status check before application: OFF",
        "status_on": "Status check before application: ON",
        "config_error": "Could not load configuration: {error}",
        "save_error": "Could not save configuration: {error}",
        "device": "{label}: device_id={device_id}",
        "response": "{label}: code={code} | {message}",
        "found_saved_session": "Detected saved Mi Account session ({source}, ID: {uid}).",
    },
}

LANG = detect_language()


def t(key: str, **kwargs) -> str:
    return TEXT.get(LANG, TEXT["en"]).get(key, TEXT["en"].get(key, key)).format(**kwargs)


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;31m"  # Crimson Red override (no orange/yellow)
    BLUE = "\033[1;34m"
    CYAN = "\033[1;37m"


def supports_color() -> bool:
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM", "") == "dumb":
        return False
    return True


def color(text: str, code: str) -> str:
    return f"{code}{text}{C.RESET}" if supports_color() else text


def log(message: str, level: str = "info") -> None:
    if _HAS_RICH:
        style_map = {
            "error": "bold #E50914",
            "ok": "bold #10B981",
            "warn": "bold #E50914",
            "info": "bold #F8FAFC",
        }
        prefix_map = {"error": "[✗]", "ok": "[✔]", "warn": "[!]", "info": "[▸]"}
        st = style_map.get(level, "bold #F8FAFC")
        pf = prefix_map.get(level, "[▸]")
        console.print(f"  [{st}]{pf}[/{st}] {message}")
        return
    codes = {"error": C.RED, "ok": C.GREEN, "warn": C.RED, "info": C.CYAN}
    prefix = {"error": "[!]", "ok": "[+]", "warn": "[*]", "info": "[>]"}
    print(color(f"{prefix.get(level, '[>]')} {message}", codes.get(level, C.CYAN)), flush=True)


def generate_device_id() -> str:
    random_data = f"{random.random()}-{time.time()}-{random.randint(0, 1000000)}"
    return hashlib.sha1(random_data.encode("utf-8")).hexdigest().upper()


def detect_saved_desktop_session() -> tuple[str, dict] | None:
    """Checks for saved Mi Account sessions in ~/.migatesession."""
    base = Path.home() / ".migatesession"
    if not base.exists():
        return None
    for sub in ["18n_bbs_global", "unlockApi", "passport"]:
        session_file = base / sub / "session.json"
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                if data.get("passToken") and data.get("userId"):
                    return sub, data
            except Exception:
                pass
    return None


def extract_token_from_saved_session() -> str | None:
    """Automatically exchange a saved `~/.migatesession` passToken for a fresh `new_bbs_serviceToken`."""
    saved = detect_saved_desktop_session()
    if not saved:
        log("No saved session found in ~/.migatesession", "warn")
        return None
    sub, auth_cookies = saved
    log(f"Extracting new_bbs_serviceToken from saved session ({sub}, UID: {auth_cookies.get('userId')})...", "info")
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json;charset=UTF-8"})
    for k, v in auth_cookies.items():
        sess.cookies.set(k, str(v))
    try:
        resp = sess.get("https://account.xiaomi.com/pass/serviceLogin", params={"sid": "18n_bbs_global", "_json": "true"}, timeout=12)
        txt = resp.text
        if txt.startswith("&&&START&&&"):
            txt = txt[11:]
        res_json = json.loads(txt)
        nonce = res_json.get("nonce")
        ssecurity = res_json.get("ssecurity")
        location = res_json.get("location")
        if nonce and ssecurity and location:
            client_sign = quote(base64.b64encode(hashlib.sha1(f"nonce={nonce}&{ssecurity}".encode()).digest()))
            sess.get(f"{location}&clientSign={client_sign}", allow_redirects=True, timeout=15)
        token = sess.cookies.get("new_bbs_serviceToken") or sess.cookies.get("serviceToken")
        if token:
            log("Successfully extracted fresh new_bbs_serviceToken!", "ok")
            return token
    except Exception as exc:
        log(f"Session token extraction failed: {exc}", "error")
    return None


def interactive_qr_or_browser_login() -> str | None:
    """
    Generate an official Xiaomi Account login URL (`18n_bbs_global`), display the clickable
    link in Termux/Terminal (and open browser if possible), and poll until the user signs in
    to automatically capture `new_bbs_serviceToken`!
    """
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json;charset=UTF-8"})
    try:
        params = {
            "sid": "18n_bbs_global",
            "_json": "false",
            "callback": "https://sgp-api.buy.mi.com/bbs/api/global/user/login-back",
        }
        resp = sess.get("https://account.xiaomi.com/longPolling/loginUrl", params=params, timeout=12)
        txt = resp.text
        if txt.startswith("&&&START&&&"):
            txt = txt[11:]
        data = json.loads(txt)
        login_url = data.get("loginUrl")
        lp_url = data.get("lp")
        timeout_sec = int(data.get("timeout", 300))
        if not login_url or not lp_url:
            log("Could not obtain Xiaomi login URL.", "error")
            return None

        if _HAS_RICH:
            console.print(
                Panel(
                    f"[bold #F8FAFC]Open this link in your browser to sign in to Xiaomi Account:[/]\n\n"
                    f"[underline bold #E50914 link={login_url}]{login_url}[/]\n\n"
                    f"[dim #94A3B8]Waiting for confirmation (up to {timeout_sec}s)... Press Ctrl+C to cancel.[/]",
                    title="[bold #E50914][ XIAOMI ACCOUNT LOGIN ][/]",
                    border_style="#E50914",
                    box=box.ROUNDED,
                )
            )
        else:
            print(f"\nOpen this URL to sign in:\n  {login_url}\nWaiting for login...")

        # Try opening in Termux or desktop browser automatically
        try:
            if os.path.exists("/data/data/com.termux/files/usr/bin/termux-open-url"):
                subprocess.Popen(["termux-open-url", login_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                import webbrowser
                webbrowser.open(login_url)
        except Exception:
            pass

        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            try:
                r_poll = sess.get(lp_url, timeout=30)
                if r_poll.status_code == 200:
                    p_txt = r_poll.text
                    if p_txt.startswith("&&&START&&&"):
                        p_txt = p_txt[11:]
                    p_data = json.loads(p_txt)
                    if p_data.get("code") == 0:
                        log("Login confirmed! Extracting new_bbs_serviceToken...", "ok")
                        nonce = p_data.get("nonce")
                        ssecurity = p_data.get("ssecurity")
                        location = p_data.get("location")
                        if location and nonce and ssecurity:
                            client_sign = quote(base64.b64encode(hashlib.sha1(f"nonce={nonce}&{ssecurity}".encode()).digest()))
                            sess.get(f"{location}&clientSign={client_sign}", allow_redirects=True, timeout=15)
                        token = sess.cookies.get("new_bbs_serviceToken") or sess.cookies.get("serviceToken")
                        if token:
                            # Also cache in ~/.migatesession/18n_bbs_global
                            try:
                                c_dict = sess.cookies.get_dict()
                                if {"deviceId", "passToken", "userId"}.issubset(c_dict.keys()):
                                    s_dir = Path.home() / ".migatesession" / "18n_bbs_global"
                                    s_dir.mkdir(parents=True, exist_ok=True)
                                    (s_dir / "session.json").write_text(
                                        json.dumps({k: c_dict[k] for k in ("deviceId", "passToken", "userId")}),
                                        encoding="utf-8",
                                    )
                            except Exception:
                                pass
                            return token
            except requests.exceptions.Timeout:
                continue
            except KeyboardInterrupt:
                log(t("interrupted"), "warn")
                return None
            except Exception:
                time.sleep(1.5)
    except Exception as exc:
        log(f"Login error: {exc}", "error")
    return None


def load_config() -> dict:
    defaults = {"cookie": "", "skip_cookie_check": False}

    if DESKTOP_CONFIG_FILE.exists():
        try:
            desktop_data = json.loads(DESKTOP_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(desktop_data, dict):
                if desktop_data.get("cookie"):
                    defaults["cookie"] = str(desktop_data["cookie"]).strip()
                if "skip_cookie_check" in desktop_data:
                    defaults["skip_cookie_check"] = bool(desktop_data["skip_cookie_check"])
        except Exception:
            pass

    try:
        if CLI_CONFIG_FILE.exists():
            cli_data = json.loads(CLI_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(cli_data, dict):
                if cli_data.get("cookie"):
                    defaults["cookie"] = str(cli_data["cookie"]).strip()
                if "skip_cookie_check" in cli_data:
                    defaults["skip_cookie_check"] = bool(cli_data["skip_cookie_check"])
    except Exception as exc:
        log(t("config_error", error=exc), "warn")

    return defaults


def save_config(config: dict) -> None:
    try:
        CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CLI_CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        log(t("save_error", error=exc), "warn")

    try:
        if DESKTOP_CONFIG_DIR.exists():
            desktop_cfg = {}
            if DESKTOP_CONFIG_FILE.exists():
                try:
                    desktop_cfg = json.loads(DESKTOP_CONFIG_FILE.read_text(encoding="utf-8"))
                except Exception:
                    desktop_cfg = {}
            desktop_cfg["cookie"] = config.get("cookie", "")
            desktop_cfg["skip_cookie_check"] = config.get("skip_cookie_check", False)
            DESKTOP_CONFIG_FILE.write_text(json.dumps(desktop_cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class XiaomiClient:
    def __init__(self, config: dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "okhttp/4.12.0",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    @staticmethod
    def cookie_header(token: str, device_id: str) -> str:
        return (
            f"new_bbs_serviceToken={token};"
            f"versionCode=500411;versionName=5.4.11;deviceId={device_id};"
        )

    def request(self, method: str, url: str, token: str, device_id: str, json_body: dict | None = None):
        headers = {
            "Cookie": self.cookie_header(token, device_id),
            "Content-Type": "application/json; charset=utf-8",
        }
        data = None
        if json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            headers["Content-Length"] = str(len(data))
        elif method.upper() == "POST":
            data = b'{"is_retry":true}'
            headers["Content-Length"] = str(len(data))

        try:
            return self.session.request(method, url, headers=headers, data=data, timeout=(5, 15))
        except requests.RequestException as exc:
            log(t("request_error", error=exc), "error")
            return None

    def check_status(self, token: str) -> bool:
        device_id = generate_device_id()
        log(t("checking"))
        response = self.request("GET", STATUS_URL, token, device_id)
        if response is None:
            return False
        try:
            data = response.json()
        except ValueError:
            log(t("bad_json"), "error")
            return False

        code = data.get("code")
        if code in (100004, 10004):
            log(t("cookie_bad"), "error")
            return False

        payload = data.get("data") or {}
        is_pass = payload.get("is_pass")
        button_state = payload.get("button_state")
        deadline = payload.get("deadline_format", "")

        if is_pass == 4 and button_state == 1:
            log(t("ready"), "ok")
            return True
        if is_pass == 4 and button_state == 2:
            log(t("blocked", value=deadline or ("не указано" if LANG == "ru" else "not specified")), "warn")
            return False
        if is_pass == 4 and button_state == 3:
            log(t("not_ready"), "warn")
            return False
        if is_pass == 1:
            log(t("approved", value=deadline or ("не указано" if LANG == "ru" else "not specified")), "ok")
            return False

        log(t("unknown_status", code=code, data=payload), "warn")
        return False

    def apply_once(self, token: str, device_id: str | None = None, label: str = "Request") -> bool:
        device_id = device_id or generate_device_id()
        log(t("device", label=label, device_id=device_id))
        response = self.request("POST", APPLY_URL, token, device_id)
        if response is None:
            return False

        try:
            result = response.json()
        except ValueError:
            log(t("bad_json_label", label=label), "error")
            return False

        code = result.get("code")
        message = result.get("message", "")
        payload = result.get("data") or {}
        log(t("response", label=label, code=code, message=message))

        if code == 0:
            apply_result = payload.get("apply_result")
            if apply_result == 1:
                log(t("apply", label=label, code=code), "ok")
                return True
            if apply_result == 3:
                deadline = payload.get("deadline_format", "не указано" if LANG == "ru" else "not specified")
                log(t("not_submitted", label=label, value=deadline), "warn")
                return False

        if code == 100003:
            log(t("maybe_approved", label=label), "ok")
            return True
        if code in (100004, 10004):
            log(t("cookie_bad"), "error")
            return False
        if code == 100001:
            log(t("rejected", label=label), "warn")
            return False

        log(t("unknown_response", label=label, result=result), "warn")
        return False


def ntp_time(server: str, timeout: float = 3.0) -> datetime | None:
    packet = b"\x1b" + 47 * b"\0"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(packet, (server, 123))
        data, _ = sock.recvfrom(48)
        if len(data) < 48:
            return None
        seconds, fraction = struct.unpack("!II", data[40:48])
        timestamp = seconds - 2208988800 + fraction / 2**32
        return datetime.fromtimestamp(timestamp, timezone.utc).astimezone(timezone(timedelta(hours=8)))
    except (OSError, struct.error):
        return None
    finally:
        sock.close()


def get_beijing_time() -> tuple[datetime, float] | tuple[None, None]:
    for server in NTP_SERVERS:
        log(t("ntp", server=server))
        current = ntp_time(server)
        local_ts = time.time()
        if current:
            log(t("beijing", value=current.strftime("%Y-%m-%d %H:%M:%S.%f")), "ok")
            return current, local_ts
    log(t("ntp_fail"), "error")
    return None, None


def tcp_ping(host: str, port: int = 443, timeout: float = 3.0) -> float | None:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (time.perf_counter() - start) * 1000
    except OSError:
        return None


def http_ping(host: str, timeout: float = 3.0) -> float | None:
    start = time.perf_counter()
    try:
        response = requests.get(
            f"https://{host}",
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed if response.status_code < 500 else None
    except requests.RequestException:
        return None


def ping_command() -> None:
    if _HAS_RICH:
        tbl = Table(title="[bold #F8FAFC]Xiaomi API & Gateway Latency Benchmark[/]", box=box.ROUNDED, border_style="#E50914")
        tbl.add_column("Gateway Host", style="bold #F8FAFC")
        tbl.add_column("Resolved IP", style="#64748B")
        tbl.add_column("TCP Handshake", justify="right", style="bold #10B981")
        tbl.add_column("HTTPS RTT", justify="right", style="bold #E50914")
        for host in PING_HOSTS:
            ip = resolve_host_smart(host) or "N/A"
            tcp = tcp_ping(host)
            http = http_ping(host)
            tbl.add_row(
                host,
                ip,
                f"{tcp:.1f} ms" if tcp is not None else "TIMEOUT",
                f"{http:.1f} ms" if http is not None else "TIMEOUT",
            )
        console.print()
        console.print(tbl)
        return

    print("\n" + color(t("ping_title"), C.BOLD))
    print("-" * 40)
    for host in PING_HOSTS:
        tcp = tcp_ping(host)
        http = http_ping(host)
        tcp_text = f"{tcp:.2f} ms" if tcp is not None else "N/A"
        http_text = f"{http:.2f} ms" if http is not None else "N/A"
        print(f"{host:24} TCP: {tcp_text:>10}   HTTP: {http_text:>10}")


def run_application(client: XiaomiClient, token: str, skip_check: bool = False) -> int:
    header(t("title"))

    if not token:
        log(t("token_empty"), "error")
        return 2

    if not skip_check:
        if not client.check_status(token):
            log(t("status_fail"), "error")
            return 1
    else:
        log(t("skip"), "warn")

    beijing, start_ts = get_beijing_time()
    if beijing is None or start_ts is None:
        return 1

    target = beijing.replace(hour=23, minute=59, second=59, microsecond=0)
    if target <= beijing:
        target += timedelta(days=1)

    delay = (target - beijing).total_seconds()
    log(t("wait", seconds=delay))

    try:
        while True:
            now_sync = beijing + timedelta(seconds=(time.time() - start_ts))
            diff = (target - now_sync).total_seconds()
            if diff <= 0:
                break
            if diff > 1.0:
                time.sleep(min(diff - 0.5, 1.0))
            else:
                time.sleep(max(0.0, min(diff, 0.01)))
    except KeyboardInterrupt:
        log(t("interrupted"), "warn")
        return 130

    # Auto Mode #2 micro-offsets matching 8.1.py
    offsets_ms = [58.6, 58.8, 59.1, 59.3, 59.5, 59.8]
    log(t("reached"), "info")

    base = target
    threads: list[threading.Thread] = []
    results: list[bool] = []
    results_lock = threading.Lock()

    def dispatch_worker(seq: int, offset_val: float, dev_id: str):
        label = f"Auto #2 HTTP #{seq} (+{offset_val:.1f}ms)" if LANG == "en" else f"Авторежим #2 HTTP #{seq} (+{offset_val:.1f}мс)"
        res = client.apply_once(token, device_id=dev_id, label=label)
        with results_lock:
            results.append(res)

    for index, offset in enumerate(offsets_ms, 1):
        send_at = base + timedelta(milliseconds=offset)
        now_sync = beijing + timedelta(seconds=(time.time() - start_ts))
        timer_delay = max(0.0, (send_at - now_sync).total_seconds())
        dev_id = generate_device_id()
        timer = threading.Timer(timer_delay, dispatch_worker, args=(index, offset, dev_id))
        threads.append(timer)
        timer.start()

    for t_worker in threads:
        t_worker.join()

    success = sum(1 for r in results if r)
    log(t("done", success=success, total=len(offsets_ms)), "ok" if success else "warn")
    return 0 if success else 1


def clear_screen() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def render_xboyrex_banner() -> None:
    """Render the signature XBOYREX Double-Edge Crimson Box UI."""
    if not _HAS_RICH:
        print("\n" + color("=== XBOYREX EDITION · XIAOMI UNLOCK TOOL v8.1 ===", C.RED))
        print(f"GitHub: {REPO_URL}\n")
        return

    hdr = Text()
    hdr.append(BIG_XBOYREX_LOGO + "\n", style="bold #E50914")
    hdr.append("XIAOMI UNLOCK TOOL BY XBOYREX", style="bold #F8FAFC")
    hdr.append(f"  v{VERSION}\n", style="#E50914")
    hdr.append("SUB-MS STRATUM-1 NTP ENGINE  •  HyperOS 1/2/3 & MIUI 14 Quota Unlocker\n", style="dim #94A3B8")
    hdr.append("Developed by xboyrex (Mayank Droid) · Official XBOYREX Edition\n", style="#64748B")
    hdr.append("GitHub: ", style="dim #94A3B8")
    hdr.append(REPO_URL, style=f"underline #E50914 link {REPO_URL}")

    console.print(
        Panel(
            hdr,
            border_style="#E50914",
            box=box.DOUBLE_EDGE,
            padding=(1, 2),
            title="[bold #F8FAFC][ XBOYREX EDITION ][/]",
            subtitle="[#64748B]MIUI & HyperOS Bootloader Unlock Suite[/]",
        )
    )


def header(title: str) -> None:
    if _HAS_RICH:
        console.print(
            Panel(
                f"[bold #F8FAFC]{title}[/]",
                border_style="#E50914",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
    else:
        print("\n" + color("╭──────────────────────────────────────╮", C.RED))
        print(color(f"│ {title:^36} │", C.RED))
        print(color("╰──────────────────────────────────────╯", C.RED))


def token_menu(client: XiaomiClient, config: dict) -> None:
    token = getpass.getpass(t("token_prompt")).strip()
    if not token:
        log(t("not_saved"), "error")
        return
    config["cookie"] = token
    save_config(config)
    log(t("saved"), "ok")


def settings_tab(client: XiaomiClient, config: dict) -> None:
    while True:
        clear_screen()
        render_xboyrex_banner()
        token = config.get("cookie", "").strip()
        check_enabled = not bool(config.get("skip_cookie_check", False))
        token_status = "✔ SET" if token else "✗ NOT SET"

        if _HAS_RICH:
            tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tbl.add_column("Key", style="bold #E50914", no_wrap=True)
            tbl.add_column("Val", style="bold #F8FAFC")
            tbl.add_row("[01]", t("settings_qr_login"))
            tbl.add_row("[02]", t("settings_session_login"))
            tbl.add_row("[03]", t("settings_set_token"))
            tbl.add_row("[04]", f"{t('settings_toggle_check')} (Current: {'ON' if check_enabled else 'OFF'})")
            tbl.add_row("[05]", t("settings_ping"))
            tbl.add_row("", "")
            tbl.add_row("[0 ]", f"[dim #94A3B8]{t('back')}[/]")

            console.print(
                Panel(
                    tbl,
                    title=f"[bold #E50914]{t('tab_settings')}  •  Token: {token_status}[/]",
                    subtitle=f"[#64748B]Config: {CLI_CONFIG_FILE}[/]",
                    border_style="#64748B",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )
            choice = console.input(f"\n[bold #E50914]▌[/] [bold #F8FAFC]{t('choose')}[/]").strip().lstrip("0") or "0"
        else:
            header(t("tab_settings"))
            print(f"{t('settings_token')}: {token_status}")
            print(f"[1] {t('settings_qr_login')}")
            print(f"[2] {t('settings_session_login')}")
            print(f"[3] {t('settings_set_token')}")
            print(f"[4] {t('settings_toggle_check')}")
            print(f"[5] {t('settings_ping')}")
            print(f"[0] {t('back')}")
            choice = input("\n" + t("choose")).strip()

        if choice == "1":
            new_tok = interactive_qr_or_browser_login()
            if new_tok:
                config["cookie"] = new_tok
                save_config(config)
                log(t("saved"), "ok")
            input("\nPress Enter...")
        elif choice == "2":
            new_tok = extract_token_from_saved_session()
            if new_tok:
                config["cookie"] = new_tok
                save_config(config)
                log(t("saved"), "ok")
            input("\nPress Enter...")
        elif choice == "3":
            token_menu(client, config)
            input("\nPress Enter...")
        elif choice == "4":
            config["skip_cookie_check"] = not config.get("skip_cookie_check", False)
            save_config(config)
            log(t("status_off") if config["skip_cookie_check"] else t("status_on"), "ok")
            time.sleep(0.8)
        elif choice == "5":
            ping_command()
            input("\nPress Enter...")
        elif choice in ("0", "b", "q"):
            return
        else:
            log(t("unknown_choice"), "warn")
            time.sleep(0.8)


def submit_tab(client: XiaomiClient, config: dict) -> None:
    while True:
        clear_screen()
        render_xboyrex_banner()
        token = config.get("cookie", "").strip()
        if _HAS_RICH:
            tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tbl.add_column("Key", style="bold #E50914", no_wrap=True)
            tbl.add_column("Val", style="bold #F8FAFC")
            tbl.add_row("[01]", t("submit_run"))
            tbl.add_row("[02]", t("submit_status"))
            tbl.add_row("[03]", t("submit_ping"))
            tbl.add_row("", "")
            tbl.add_row("[0 ]", f"[dim #94A3B8]{t('back')}[/]")
            console.print(
                Panel(
                    tbl,
                    title=f"[bold #E50914]{t('tab_submit')}  •  Token: {'✔' if token else '✗'}[/]",
                    subtitle=f"[link={REPO_URL}][#64748B]How It Works: {REPO_URL}[/][/link]",
                    border_style="#64748B",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )
            choice = console.input(f"\n[bold #E50914]▌[/] [bold #F8FAFC]{t('choose')}[/]").strip().lstrip("0") or "0"
        else:
            header(t("tab_submit"))
            print(f"[1] {t('submit_run')}")
            print(f"[2] {t('submit_status')}")
            print(f"[3] {t('submit_ping')}")
            print(f"[0] {t('back')}")
            choice = input("\n" + t("choose")).strip()

        if choice == "1":
            if not token:
                token = extract_token_from_saved_session() or getpass.getpass(t("token_prompt")).strip()
                if token:
                    config["cookie"] = token
                    save_config(config)
            if token:
                run_application(client, token, bool(config.get("skip_cookie_check", False)))
            input("\nPress Enter...")
        elif choice == "2":
            if not token:
                token = extract_token_from_saved_session() or getpass.getpass(t("token_prompt")).strip()
            if token:
                config["cookie"] = token
                save_config(config)
                client.check_status(token)
            input("\nPress Enter...")
        elif choice == "3":
            ping_command()
            input("\nPress Enter...")
        elif choice in ("0", "b", "q"):
            return
        else:
            log(t("unknown_choice"), "warn")
            time.sleep(0.8)


def find_miunlock() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "miunlock", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True, sys.executable
    except (OSError, subprocess.SubprocessError):
        pass
    return False, sys.executable


def install_and_run_miunlock() -> None:
    installed, python_cmd = find_miunlock()
    if not installed:
        log(t("mi_installing"), "info")
        try:
            result = subprocess.run(
                [python_cmd, "-m", "pip", "install", "-U", "miunlock"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                log(t("mi_install_failed"), "error")
                if result.stderr:
                    print(result.stderr[-1200:])
                return
        except (OSError, subprocess.SubprocessError) as exc:
            log(t("mi_install_failed"), "error")
            print(str(exc))
            return

    log(t("mi_launching"), "info")
    try:
        result = subprocess.run([python_cmd, "-m", "miunlock"])
        if result.returncode != 0:
            log(t("mi_launch_failed", error=f"exit code {result.returncode}"), "error")
    except (OSError, subprocess.SubprocessError) as exc:
        log(t("mi_launch_failed", error=exc), "error")


def miunlock_tab(client: XiaomiClient, config: dict) -> None:
    while True:
        clear_screen()
        render_xboyrex_banner()
        installed, python_cmd = find_miunlock()
        if _HAS_RICH:
            tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tbl.add_column("Key", style="bold #E50914", no_wrap=True)
            tbl.add_column("Val", style="bold #F8FAFC")
            tbl.add_row("[01]", t("mi_install_run"))
            tbl.add_row("[02]", f"{t('mi_status')} ({t('installed') if installed else t('not_installed')})")
            tbl.add_row("", "")
            tbl.add_row("[0 ]", f"[dim #94A3B8]{t('back')}[/]")
            console.print(
                Panel(
                    tbl,
                    title=f"[bold #E50914]{t('tab_miunlock')}[/]",
                    subtitle=f"[#64748B]{t('mi_note')}[/]",
                    border_style="#64748B",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )
            choice = console.input(f"\n[bold #E50914]▌[/] [bold #F8FAFC]{t('choose')}[/]").strip().lstrip("0") or "0"
        else:
            header(t("tab_miunlock"))
            print(f"[1] {t('mi_install_run')}")
            print(f"[2] {t('mi_status')}")
            print(f"[0] {t('back')}")
            choice = input("\n" + t("choose")).strip()

        if choice == "1":
            install_and_run_miunlock()
            input("\nPress Enter...")
        elif choice == "2":
            installed, _ = find_miunlock()
            log(t("installed") if installed else t("not_installed"), "ok" if installed else "warn")
            input("\nPress Enter...")
        elif choice in ("0", "b", "q"):
            return
        else:
            log(t("unknown_choice"), "warn")
            time.sleep(0.8)


def interactive(client: XiaomiClient, config: dict) -> int:
    saved_session = detect_saved_desktop_session()
    if saved_session and not config.get("cookie"):
        tok = extract_token_from_saved_session()
        if tok:
            config["cookie"] = tok
            save_config(config)

    while True:
        clear_screen()
        render_xboyrex_banner()

        if _HAS_RICH:
            tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            tbl.add_column("Stage", style="bold #E50914", no_wrap=True)
            tbl.add_column("Title", style="bold #F8FAFC")
            tbl.add_row("[01]", t("tab_settings"))
            tbl.add_row("[02]", t("tab_submit"))
            tbl.add_row("[03]", t("tab_miunlock"))
            tbl.add_row("", "")
            tbl.add_row("[Q ]", f"[dim #94A3B8]{t('menu_exit')}[/]")

            console.print(
                Panel(
                    tbl,
                    title="[bold #E50914]Execution Pipeline[/]",
                    subtitle=f"[link={REPO_URL}][#64748B]How It Works: {REPO_URL}[/][/link]",
                    border_style="#64748B",
                    box=box.ROUNDED,
                    padding=(0, 2),
                )
            )
            raw = console.input(f"\n[bold #E50914]▌[/] [bold #F8FAFC]{t('select_tab')}[/]").strip().lower()
        else:
            header(t("title"))
            print(f"[1] {t('tab_settings')}")
            print(f"[2] {t('tab_submit')}")
            print(f"[3] {t('tab_miunlock')}")
            print(f"[0] {t('menu_exit')}")
            raw = input("\n" + t("select_tab")).strip().lower()

        choice = raw.lstrip("0") or "0"
        if choice in ("0", "q", "quit", "exit"):
            return 0
        if choice == "1":
            settings_tab(client, config)
        elif choice == "2":
            submit_tab(client, config)
        elif choice == "3":
            miunlock_tab(client, config)
        else:
            log(t("unknown_choice"), "warn")
            time.sleep(0.8)


def build_parser() -> argparse.ArgumentParser:
    description = "Xiaomi Unlock Tool 8.1 (XBOYREX Edition) — Sub-ms NTP Quota & Bootloader Unlocker"
    token_help = "New_bbs_ServiceToken"
    skip_help = "Skip preliminary account status check"
    run_help = "Run the application submission process (Auto Mode #2)"
    status_help = "Check account status"
    ping_help = "Check Xiaomi API TCP/HTTP latency"
    token_cmd_help = "Set ServiceToken interactively"
    config_help = "Show configuration file paths"

    common_parent = argparse.ArgumentParser(add_help=False)
    common_parent.add_argument("--token", help=token_help, default=argparse.SUPPRESS)
    common_parent.add_argument("--skip-status-check", action="store_true", help=skip_help, default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(
        prog="miunlocktool",
        description=description,
        parents=[common_parent],
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION} (xboyrex Edition)")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("run", help=run_help, parents=[common_parent])
    sub.add_parser("status", help=status_help, parents=[common_parent])
    sub.add_parser("ping", help=ping_help)
    sub.add_parser("token", help=token_cmd_help)
    sub.add_parser("login", help="Sign in via Xiaomi Account QR / Browser URL")
    sub.add_parser("config", help=config_help)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()
    client = XiaomiClient(config)

    if args.command == "config":
        print(f"CLI Config:     {CLI_CONFIG_FILE}")
        if DESKTOP_CONFIG_FILE.exists():
            print(f"Desktop Config: {DESKTOP_CONFIG_FILE}")
        return 0

    if args.command == "ping":
        render_xboyrex_banner()
        ping_command()
        return 0

    if args.command == "login":
        render_xboyrex_banner()
        tok = interactive_qr_or_browser_login()
        if tok:
            config["cookie"] = tok
            save_config(config)
            log(t("saved"), "ok")
            return 0
        return 1

    if args.command == "token":
        token = getpass.getpass(t("token_prompt")).strip()
        if not token:
            log(t("not_saved"), "error")
            return 2
        config["cookie"] = token
        save_config(config)
        log(t("saved"), "ok")
        return 0

    token = (getattr(args, "token", None) or config.get("cookie", "")).strip()

    if args.command == "status":
        render_xboyrex_banner()
        if not token:
            token = extract_token_from_saved_session() or getpass.getpass(t("token_prompt")).strip()
        return 0 if token and client.check_status(token) else 1

    if args.command == "run":
        render_xboyrex_banner()
        skip_status = getattr(args, "skip_status_check", False) or bool(config.get("skip_cookie_check", False))
        if not token:
            token = extract_token_from_saved_session() or ""
        return run_application(client, token, skip_status)

    return interactive(client, config)


if __name__ == "__main__":
    raise SystemExit(main())
