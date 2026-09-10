import yfinance as yf
import pandas as pd
import json
import time

from datetime import datetime
from zoneinfo import ZoneInfo

from tickers import TICKERS


# =========================================================
# TIMESTAMP
# =========================================================

TZ_WIB = ZoneInfo("Asia/Jakarta")

START_TIME = time.perf_counter()

RUN_STARTED = datetime.now(
    TZ_WIB
).strftime("%Y-%m-%d %H:%M:%S")


# =========================
# VALUE FORMATTER
# =========================

def format_value(x):

    if x >= 1_000_000_000_000:
        return f"{x/1_000_000_000_000:.2f}T"

    elif x >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}B"

    elif x >= 1_000_000:
        return f"{x/1_000_000:.2f}M"

    else:
        return f"{x:.0f}"


# =========================================================
# CORE ENGINE — TIDAK DIUBAH
# =========================================================

def ema(series, length):

    return series.ewm(
        span=length,
        adjust=False
    ).mean()


def calc_macd(close):

    ema_fast = ema(
        close,
        12
    )

    ema_slow = ema(
        close,
        26
    )

    macd = ema_fast - ema_slow

    signal = ema(
        macd,
        9
    )

    hist = macd - signal

    return (
        macd,
        signal,
        hist
    )


def hist_age(hist_series):

    streak = 1

    last = hist_series.iloc[-1]

    last_dir = (
        "green"
        if last >= 0
        else "red"
    )

    for i in range(
        len(hist_series) - 2,
        -1,
        -1
    ):

        cur_dir = (
            "green"
            if hist_series.iloc[i] >= 0
            else "red"
        )

        if cur_dir == last_dir:

            streak += 1

        else:

            break

    return (
        f"+{streak}"
        if last_dir == "green"
        else f"-{streak}"
    )


def ema20_break_age(
    close,
    ema_series
):

    last_idx = None

    last_type = None

    for i in range(
        1,
        len(close)
    ):

        if (
            close.iloc[i-1]
            <= ema_series.iloc[i-1]
            and
            close.iloc[i]
            > ema_series.iloc[i]
        ):

            last_idx = i

            last_type = "UP"

        elif (
            close.iloc[i-1]
            >= ema_series.iloc[i-1]
            and
            close.iloc[i]
            < ema_series.iloc[i]
        ):

            last_idx = i

            last_type = "DOWN"


    if last_idx is None:

        return "NO CROSS"


    age = (
        len(close)
        - 1
        - last_idx
        + 1
    )


    return (
        f"+{age}"
        if last_type == "UP"
        else f"-{age}"
    )


def quality_score(
    hist_age_str,
    spike_ratio,
    macd_hist,
    hist_series
):

    score = 0

    penalty = 0

    hist_num = int(
        hist_age_str.replace(
            "+",
            ""
        )
    )


    if hist_num <= 2:

        score += 3

    elif hist_num <= 4:

        score += 2

    elif hist_num <= 6:

        score += 1


    if spike_ratio <= 1.5:

        score += 3

    elif spike_ratio <= 2.5:

        score += 2

    elif spike_ratio <= 3.5:

        score += 1

    else:

        penalty += 1


    if spike_ratio > 5:

        penalty += 2


    hist_mean20 = (
        hist_series
        .iloc[-21:-1]
        .abs()
        .mean()
    )


    if hist_mean20 == 0:

        return "LOW"


    macd_strength = (
        abs(macd_hist)
        / hist_mean20
    )


    if macd_strength >= 1.5:

        score += 3

    elif macd_strength >= 1.0:

        score += 2

    elif macd_strength >= 0.5:

        score += 1

    else:

        penalty += 1


    final_score = (
        score - penalty
    )


    if final_score >= 6:

        return "HIGH"

    elif final_score >= 3:

        return "MED"

    else:

        return "LOW"


# =========================================================
# MAIN LOOP
# =========================================================

results = []

total = len(TICKERS)

processed = 0

errors = 0


print(
    "========================================"
)

print(
    "MACD SCANNER"
)

print(
    "========================================"
)

print(
    "Total ticker :",
    total
)

print(
    "Started      :",
    RUN_STARTED
)

print(
    "========================================"
)

print()


for number, t in enumerate(
    TICKERS,
    1
):

    print(
        f"[{number}/{total}] {t}",
        flush=True
    )

    try:

        df = None

        last_error = None

        for attempt in range(1, 4):

            try:

                df = (
                    yf.Ticker(t)
                    .history(
                        period="400d"
                    )
                    .dropna()
                )

                if not df.empty:
                    break

            except Exception as e:

                last_error = e

            time.sleep(0.5 * attempt)

        if df is None or df.empty:

            if last_error:
                raise last_error

            processed += 1

            continue


        close = df["Close"]

        volume = df["Volume"]


        returns = (
            close.pct_change()
        )


        Rt = returns.iloc[-1]

        R_mean20 = (
            returns
            .iloc[-21:-1]
            .abs()
            .mean()
        )


        if R_mean20 == 0:

            processed += 1

            continue


        spike_ratio = (
            abs(Rt)
            / R_mean20
        )


        last_price = (
            close.iloc[-1]
        )

        last_volume = (
            volume.iloc[-1]
        )


        value = (
            last_price
            * last_volume
        )


        if value < 5_000_000_000:

            processed += 1

            continue


        ema20_series = ema(
            close,
            20
        )

        ema20 = (
            ema20_series.iloc[-1]
        )


        macd, signal, hist = (
            calc_macd(close)
        )

        last_hist = (
            hist.iloc[-1]
        )


        if not (
            last_price > ema20
            and
            last_hist > 0
        ):

            processed += 1

            continue


        ema20_age = (
            ema20_break_age(
                close,
                ema20_series
            )
        )


        if ema20_age != "+1":

            processed += 1

            continue


        h_age = hist_age(hist)


        hist_num = int(
            h_age.replace(
                "+",
                ""
            )
        )


        if hist_num > 6:

            processed += 1

            continue


        quality = quality_score(
            h_age,
            spike_ratio,
            last_hist,
            hist
        )


        results.append({

            "Ticker":
                t,

            "Price":
                last_price,

            "EMA20":
                ema20,

            "MACD_Hist":
                last_hist,

            "Hist_Age":
                h_age,

            "Spike_Ratio":
                spike_ratio,

            "EMA20_Break_Age":
                ema20_age,

            "Value":
                value,

            "Value_Str":
                format_value(value),

            "Quality":
                quality

        })


        processed += 1


    except Exception as e:

        errors += 1

        processed += 1

        print(
            f"  ERROR: {t} -> {e}",
            flush=True
        )

        continue

    finally:

        time.sleep(0.15)


# =========================================================
# OUTPUT
# =========================================================

df = pd.DataFrame(results)


if not df.empty:

    df["Hist_Num"] = (
        df["Hist_Age"]
        .str.replace(
            "+",
            "",
            regex=False
        )
        .astype(int)
    )


    df = df.sort_values(
        by=[
            "Hist_Num",
            "Spike_Ratio"
        ],
        ascending=[
            True,
            True
        ]
    )


    df = df.drop(
        columns=[
            "Hist_Num",
            "Value"
        ]
    )


    for col in [
        "Price",
        "EMA20",
        "MACD_Hist",
        "Spike_Ratio"
    ]:

        df[col] = (
            df[col]
            .astype(float)
            .round(2)
        )


    df = df[

        [
            "Ticker",
            "Price",
            "Spike_Ratio",
            "Hist_Age",
            "MACD_Hist",
            "Value_Str",
            "EMA20",
            "EMA20_Break_Age",
            "Quality"
        ]

    ]


# =========================================================
# FINISH
# =========================================================

END_TIME = time.perf_counter()

RUN_FINISHED = datetime.now(
    TZ_WIB
).strftime("%Y-%m-%d %H:%M:%S")


DURATION_SECONDS = round(
    END_TIME - START_TIME,
    1
)


minutes = int(
    DURATION_SECONDS // 60
)

seconds = int(
    DURATION_SECONDS % 60
)


DURATION_TEXT = (
    f"{minutes}m {seconds}s"
)


# =========================================================
# JSON OUTPUT
# =========================================================

macd_results = {

    "status":
        "success",

    "generated_at":
        RUN_FINISHED,

    "started_at":
        RUN_STARTED,

    "finished_at":
        RUN_FINISHED,

    "duration_seconds":
        DURATION_SECONDS,

    "duration_text":
        DURATION_TEXT,

    "total_tickers":
        total,

    "processed":
        processed,

    "errors":
        errors,

    "candidates":
        len(df),

    "data":
        []

}


if not df.empty:

    for _, row in df.iterrows():

        macd_results["data"].append({

            "ticker":
                row["Ticker"],

            "price":
                float(row["Price"]),

            "spike_ratio":
                float(row["Spike_Ratio"]),

            "hist_age":
                row["Hist_Age"],

            "macd_hist":
                float(row["MACD_Hist"]),

            "value":
                row["Value_Str"],

            "ema20":
                float(row["EMA20"]),

            "ema20_break_age":
                row["EMA20_Break_Age"],

            "quality":
                row["Quality"]

        })


with open(
    "macd_results.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        macd_results,
        f,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# CONSOLE
# =========================================================

print()

print(
    "========================================"
)

print(
    "MACD SCAN FINISHED"
)

print(
    "========================================"
)

print(
    "Candidates :",
    len(df)
)

print(
    "Processed  :",
    processed,
    "/",
    total
)

print(
    "Errors     :",
    errors
)

print(
    "Duration   :",
    DURATION_TEXT
)

print(
    "Finished   :",
    RUN_FINISHED
)

print(
    "Result saved to macd_results.json"
)
