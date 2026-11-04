from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

import pandas as pd
import pdfplumber


ROOT = Path(__file__).resolve().parent
RAW = ROOT
PROCESSED = ROOT

GENERIC_LABELS = {
    "Average",
    "Weekday",
    "Saturday",
    "Sunday",
    "Annual",
    "Total",
    "Entries",
    "Rides",
    "Last",
    "Yr",
    "Cur",
    "%",
    "Chg",
    "Note:",
    "Route",
    "Page",
    "Calendar",
    "Year",
    "indicates",
    "station/entrance",
    "is",
    "accessible",
}


def group_rows(page: pdfplumber.page.Page) -> list[list[dict]]:
    words = page.extract_words(
        x_tolerance=2,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=True,
    )
    grouped: dict[float, list[dict]] = defaultdict(list)
    for word in words:
        grouped[round(word["top"] / 3) * 3].append(word)
    return [
        sorted(grouped[top], key=lambda word: word["x0"])
        for top in sorted(grouped)
    ]


def row_text(words: list[dict]) -> str:
    return " ".join(word["text"] for word in words)


def numeric_columns(words: list[dict]) -> tuple[int | None, int | None]:
    previous = None
    current = None

    for word in words:
        token = word["text"].replace(",", "")
        if "%" in token or not re.fullmatch(r"-?\d+(?:\.\d+)?", token):
            continue
        value = int(float(token))
        if 580 <= word["x0"] < 628:
            previous = value
        elif 628 <= word["x0"] < 662:
            current = value

    return previous, current


def normalize_line(line: str) -> str:
    lowered = line.lower()
    for color in ("red", "blue", "brown", "green", "orange", "pink", "purple", "yellow"):
        if color in lowered:
            return color.title()
    if "loop" in lowered:
        return "Loop"
    return line.strip()


def canonical_station_name(name: str) -> str:
    line_suffix = re.compile(
        r"\s+(?:(?:Red|Blue|Brown|Green|Orange|Pink|Purple|Yellow),?\s*)+$"
    )
    name = line_suffix.sub("", name)
    name = re.sub(r"\s+\(Main Entrance\)$", "", name, flags=re.IGNORECASE)
    return name.strip(" ,")


def extract_year(pdf_path: Path, first_page: int) -> pd.DataFrame:
    records: list[dict] = []
    station: str | None = None
    current_line = ""
    pending_station_total = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[first_page - 1 :]:
            for words in group_rows(page):
                text = row_text(words)
                labels = [word for word in words if word["x0"] < 230]
                label_text = " ".join(word["text"] for word in labels)
                station_start = [
                    word
                    for word in words
                    if 95 <= word["x0"] < 112
                ]
                station_words = list(station_start)
                if station_start:
                    station_words.extend(
                        word
                        for word in words
                        if 112 <= word["x0"] < 190
                    )
                station_text = " ".join(word["text"] for word in station_words)
                x85_text = " ".join(
                    word["text"] for word in words if 70 <= word["x0"] < 90
                )
                data = [word for word in words if word["x0"] >= 270]
                previous, current = numeric_columns(words) if data else (None, None)

                if not data:
                    if label_text.startswith("Station Total"):
                        pending_station_total = True
                        continue
                    if "Line" in label_text and "Total" not in label_text:
                        if x85_text:
                            current_line = normalize_line(label_text)
                        continue
                    if label_text == "Loop":
                        current_line = "Loop"
                        continue
                    if (
                        station_text
                        and "Line" not in station_text
                        and "Total" not in station_text
                        and not any(
                            token in GENERIC_LABELS
                            for token in station_text.split()
                        )
                    ):
                        station = canonical_station_name(station_text)
                    continue

                if label_text.startswith("Station Total") or pending_station_total:
                    if station and current is not None:
                        records.append(
                            {
                                "station": station,
                                "line": current_line,
                                "entries_previous_year": previous,
                                "entries_current_year": current,
                            }
                        )
                    pending_station_total = False
                    continue

                if (
                    station_text
                    and "Line" not in station_text
                    and "Total" not in station_text
                    and not any(
                        token in GENERIC_LABELS for token in station_text.split()
                    )
                ):
                    station = canonical_station_name(station_text)
                    if current is not None:
                        records.append(
                            {
                                "station": station,
                                "line": current_line,
                                "entries_previous_year": previous,
                                "entries_current_year": current,
                            }
                        )

    frame = pd.DataFrame(records).dropna(subset=["entries_current_year"])
    frame = frame.groupby(["station", "line"], as_index=False).max()
    return frame


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    reports = {
        2019: (RAW / "2019_Annual_Ridership_Report.pdf", 12),
        2025: (RAW / "2025_Annual_Ridership_Report.pdf", 14),
    }
    frames = {}
    for year, (path, first_page) in reports.items():
        frame = extract_year(path, first_page)
        frame = frame.rename(
            columns={
                "entries_previous_year": f"entries_{year - 1}",
                "entries_current_year": f"entries_{year}",
            }
        )
        frames[year] = frame
        print(f"{year}: {len(frame)} station rows")
        frame.to_csv(
            PROCESSED / f"cta_station_entries_{year}.csv",
            index=False,
        )

    combined = frames[2019].merge(
        frames[2025][["station", "line", "entries_2025"]],
        on=["station", "line"],
        how="inner",
    )
    combined["recovery_pct"] = combined["entries_2025"] / combined["entries_2019"] * 100
    combined = combined[combined["entries_2019"] >= 100_000].copy()
    combined["comparable"] = ~combined["station"].isin(["Berwyn", "Lawrence"])
    combined["analysis_note"] = ""
    combined.loc[
        ~combined["comparable"],
        "analysis_note",
    ] = "Reopened July 20, 2025; annual entries reflect partial-year service."
    combined.sort_values("recovery_pct", inplace=True)
    combined = combined[
        [
            "station",
            "line",
            "entries_2019",
            "entries_2025",
            "recovery_pct",
            "comparable",
            "analysis_note",
        ]
    ]

    output = PROCESSED / "cta_station_recovery.csv"
    combined.to_csv(output, index=False)
    print(f"Wrote {len(combined)} stations after the 2019 base threshold to {output}")
    print(combined.head(12).to_string(index=False))
    print(combined.tail(12).to_string(index=False))


if __name__ == "__main__":
    main()
