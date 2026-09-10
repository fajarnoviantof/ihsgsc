import yfinance as yf
import pandas as pd
import json
import math
import time

from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# TIMESTAMP & TIMER
# =========================================================

TZ_WIB = ZoneInfo("Asia/Jakarta")

START_TIME = time.perf_counter()

RUN_STARTED = datetime.now(
    TZ_WIB
).strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# LOAD DAILY OHLC
# =========================================================

def load_ohlc_yahoo(ticker, period="3mo", retries=3, delay=2.0):

    last_error = None

    for attempt in range(1, retries + 1):

        try:

            df = yf.download(
                ticker,
                interval="1d",
                period=period,
                auto_adjust=False,
                progress=False
            )

            if df.empty:
                raise ValueError("Empty data")

            break

        except Exception as e:

            last_error = e

            if attempt == retries:
                raise

            time.sleep(delay * attempt)

    else:
        raise ValueError(last_error or "Empty data")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close"
    })

    df = df[[
        "open",
        "high",
        "low",
        "close"
    ]].dropna()

    df.reset_index(
        drop=True,
        inplace=True
    )

    return df


# =========================================================
# GENCLASH ENGINE — DO NOT TOUCH
# =========================================================

def genclash_engine(df, n=5):

    top_fractal = None
    bottom_fractal = None
    last_red = None
    last_green = None
    last_fractal = None
    last_break = None
    last_order_block = None

    for i in range(len(df)):

        o, h, l, c = map(
            float,
            df.iloc[i][[
                "open",
                "high",
                "low",
                "close"
            ]]
        )

        if c < o:

            last_red = {
                "index": i,
                "open": o,
                "high": h,
                "low": l,
                "close": c
            }

        if c > o:

            last_green = {
                "index": i,
                "open": o,
                "high": h,
                "low": l,
                "close": c
            }

        if i >= n and i + n < len(df):

            if all(
                df.iloc[i].high > df.iloc[i-k].high
                and df.iloc[i].high > df.iloc[i+k].high
                for k in range(1, n + 1)
            ):

                top_fractal = {
                    "type": "UP",
                    "index": i,
                    **df.iloc[i].to_dict()
                }

                last_fractal = top_fractal

            if all(
                df.iloc[i].low < df.iloc[i-k].low
                and df.iloc[i].low < df.iloc[i+k].low
                for k in range(1, n + 1)
            ):

                bottom_fractal = {
                    "type": "DOWN",
                    "index": i,
                    **df.iloc[i].to_dict()
                }

                last_fractal = bottom_fractal

        if top_fractal and i > top_fractal["index"]:

            if (
                h > top_fractal["high"]
                or c > top_fractal["high"]
            ):

                last_break = {
                    "direction": "BULLISH",
                    "break_index": i
                }

                if last_red:

                    last_order_block = {
                        "type": "DEMAND",
                        **last_red
                    }

                top_fractal = None

        if bottom_fractal and i > bottom_fractal["index"]:

            if (
                l < bottom_fractal["low"]
                or c < bottom_fractal["low"]
            ):

                last_break = {
                    "direction": "BEARISH",
                    "break_index": i
                }

                if last_green:

                    last_order_block = {
                        "type": "SUPPLY",
                        **last_green
                    }

                bottom_fractal = None

    return (
        last_fractal,
        last_break,
        last_order_block
    )


# =========================================================
# HELPERS
# =========================================================

def calc_distance_pct(last_close, ob):

    return round(
        (
            (last_close - ob["high"])
            / ob["high"]
        ) * 100,
        2
    )


def calc_ob_size_pct(ob, last_close):

    return round(
        (
            (ob["high"] - ob["low"])
            / last_close
        ) * 100,
        2
    )


def calc_sl_price_and_pct(ob):

    r = (
        ob["high"]
        - ob["low"]
    )

    sl = (
        ob["low"]
        - (r * 0.02)
    )

    sl_pct = round(
        (
            (ob["high"] - sl)
            / ob["high"]
        ) * 100,
        2
    )

    return sl, sl_pct


def calc_tp_price_and_pct(
    ob,
    fractal
):

    tp = fractal["high"]

    tp_pct = round(
        (
            (tp - ob["high"])
            / ob["high"]
        ) * 100,
        2
    )

    return tp, tp_pct


# =========================================================
# SCORING
# =========================================================

def calc_score(
    distance,
    tp,
    sl,
    bos_age,
    ob_size
):

    s1 = max(
        0,
        30 - abs(distance)
    )

    s2 = min(
        tp * 3,
        25
    )

    s3 = max(
        0,
        15 - sl
    )

    s4 = max(
        0,
        15 - bos_age
    )

    s5 = max(
        0,
        15 - ob_size
    )

    return round(
        s1 + s2 + s3 + s4 + s5,
        2
    )


# =========================================================
# OB TOUCH COUNT
# =========================================================

def calc_ob_touch_count(
    df,
    ob,
    bos_index
):

    count = 0

    for i in range(
        bos_index + 1,
        len(df)
    ):

        h, l = df.iloc[i][[
            "high",
            "low"
        ]]

        if (
            ob["type"] == "DEMAND"
            and l <= ob["high"]
        ):

            count += 1

        if (
            ob["type"] == "SUPPLY"
            and h >= ob["low"]
        ):

            count += 1

    return count


# =========================================================
# LOAD TICKERS
# =========================================================

from tickers import TICKERS


# =========================================================
# RUN SCANNER
# =========================================================

rows = []

total = len(TICKERS)

processed = 0

errors = 0

print("========================================")
print("SMC OB SCANNER")
print("========================================")
print("Total ticker :", total)
print("Started      :", RUN_STARTED)
print("========================================")
print()


for number, ticker in enumerate(
    TICKERS,
    1
):

    print(
        f"[{number}/{total}] {ticker}",
        flush=True
    )

    try:

        df = load_ohlc_yahoo(
            ticker
        )

        fractal, brk, ob = (
            genclash_engine(df)
        )

        if not all([
            fractal,
            brk,
            ob
        ]):

            processed += 1

            continue

        last_close = float(
            df.iloc[-1].close
        )

        distance = (
            calc_distance_pct(
                last_close,
                ob
            )
        )

        ob_size = (
            calc_ob_size_pct(
                ob,
                last_close
            )
        )

        bos_age = (
            len(df)
            - 1
            - brk["break_index"]
        )

        tp, tp_pct = (
            calc_tp_price_and_pct(
                ob,
                fractal
            )
        )

        sl, sl_pct = (
            calc_sl_price_and_pct(
                ob
            )
        )

        rr = (
            round(
                tp_pct / sl_pct,
                2
            )
            if sl_pct
            else 0
        )

        ob_touch = (
            calc_ob_touch_count(
                df,
                ob,
                brk["break_index"]
            )
        )

        score = (
            calc_score(
                distance,
                tp_pct,
                sl_pct,
                bos_age,
                ob_size
            )
        )

        rows.append({

            "Ticker":
                ticker,

            "OB Type":
                ob["type"],

            "Distance":
                distance,

            "OB Range":
                f"{int(round(ob['high']))}-"
                f"{int(round(ob['low']))}",

            "TP Price":
                round(tp, 0),

            "SL Price":
                math.floor(sl),

            "TP Percent":
                round(tp_pct, 1),

            "SL Percent":
                round(sl_pct, 1),

            "BOS Age":
                bos_age,

            "OB Size":
                ob_size,

            "OB Touch":
                ob_touch,

            "RR":
                rr,

            "Score":
                score

        })

        processed += 1

    except Exception as e:

        errors += 1

        processed += 1

        print(
            f"  ERROR: {ticker} -> {e}"
        )

        continue

    finally:

        time.sleep(0.15)


# =========================================================
# DATAFRAME
# =========================================================

df = pd.DataFrame(rows)


if df.empty:

    final = pd.DataFrame()

else:

    final = (

        df[

            (df["OB Type"] == "DEMAND")

            &

            (df["Distance"] > 0)

            &

            (df["Distance"] <= 5)

            &

            (df["BOS Age"] > 0)

            &

            (df["BOS Age"] <= 10)

            &

            (df["OB Touch"] == 0)

            &

            (df["RR"] >= 2)

        ]

        .sort_values(
            "Score",
            ascending=False
        )

        .head(10)

    )


# =========================================================
# FINISH TIME
# =========================================================

END_TIME = time.perf_counter()

RUN_FINISHED = datetime.now(
    TZ_WIB
).strftime(
    "%Y-%m-%d %H:%M:%S"
)

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
# CONVERT TO WEB JSON
# =========================================================

results = {

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
        len(final),

    "data":
        []

}


if not final.empty:

    for _, row in final.iterrows():

        results["data"].append({

            "ticker":
                row["Ticker"],

            "ob_range":
                row["OB Range"],

            "sl":
                row["SL Price"],

            "sl_pct":
                row["SL Percent"],

            "tp":
                row["TP Price"],

            "tp_pct":
                row["TP Percent"],

            "rr":
                row["RR"],

            "distance":
                row["Distance"],

            "bos_age":
                int(
                    row["BOS Age"]
                ),

            "ob_size":
                row["OB Size"],

            "score":
                row["Score"]

        })


# =========================================================
# SAVE RESULT
# =========================================================

with open(
    "results.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# CONSOLE
# =========================================================

print()
print("========================================")
print("SCAN FINISHED")
print("========================================")
print(
    "Candidates :",
    len(final)
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
    "Result saved to results.json"
)
