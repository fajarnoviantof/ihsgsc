import argparse, json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jakarta")
HISTORY_FILE = Path("history.json")
KEEP_DAYS = 31

# Slot jam yang dipantau. Kalau sebuah run selesai di luar jam-jam ini
# (mis. delay sampai jam 20.20), hasilnya TIDAK diarsipkan sama sekali.
VALID_SLOTS = {
    "09:00", "10:00", "11:00",
    "13:00", "14:00", "15:00", "16:00", "17:00"
}


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf8"))
    except Exception:
        return None


def slot_from_timestamp(ts):
    """Tentukan slot jam berdasarkan waktu SELESAI run itu sendiri.
    Contoh: selesai 14.22 atau 14.55 -> masuk slot '14:00'.
    Kalau di luar VALID_SLOTS (mis. selesai jam 20.20), return None
    supaya tidak diarsipkan."""

    if not ts:
        return None

    ts = str(ts)

    if len(ts) < 13:
        return None

    hour = ts[11:13]
    slot = f"{hour}:00"

    return slot if slot in VALID_SLOTS else None


def add(h, scanner, payload):

    if not payload:
        return

    ts = payload.get("generated_at") or payload.get("finished_at")

    slot = slot_from_timestamp(ts)

    if not slot:
        # Run selesai di luar jam trading yang dipantau -> abaikan,
        # biarkan slot yang bersangkutan tetap kosong di tampilan.
        return

    date = str(ts)[:10]

    # Hapus entri lama untuk scanner+slot+tanggal yang sama supaya
    # tidak dobel kalau ada run susulan yang kebetulan selesai di
    # jam yang sama.
    h[:] = [
        x for x in h
        if not (
            x.get("scanner") == scanner
            and x.get("slot") == slot
            and str(x.get("generated_at", ""))[:10] == date
        )
    ]

    h.append({
        "scanner": scanner,
        "slot": slot,
        "generated_at": ts,
        "candidates": payload.get("candidates", 0),
        "total_tickers": payload.get("total_tickers", 0),
        "processed": payload.get("processed", 0),
        "errors": payload.get("errors", 0),
        "duration_text": payload.get("duration_text"),
        "data": payload.get("data", [])
    })


def main():

    p = argparse.ArgumentParser()
    p.add_argument("--ob", default="skipped")
    p.add_argument("--macd", default="skipped")
    a = p.parse_args()

    old = load(HISTORY_FILE) or {}
    h = old.get("history", []) if isinstance(old, dict) else []

    if a.ob == "success":
        add(h, "SMC OB", load("results.json"))

    if a.macd == "success":
        add(h, "MACD", load("macd_results.json"))

    cutoff = datetime.now(TZ) - timedelta(days=KEEP_DAYS)

    def still_fresh(x):
        ts = str(x.get("generated_at", ""))[:19]
        try:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ) >= cutoff
        except ValueError:
            return False

    h = [x for x in h if still_fresh(x)]
    h.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

    HISTORY_FILE.write_text(
        json.dumps({
            "updated_at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "keep_days": KEEP_DAYS,
            "slots": sorted(VALID_SLOTS),
            "history": h
        }, ensure_ascii=False, indent=2),
        encoding="utf8"
    )


if __name__ == "__main__":
    main()
