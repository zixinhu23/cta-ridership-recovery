from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "cta_station_recovery.csv"
FIGURE = ROOT / "cta_recovery.png"


def load_station_recovery(path: Path) -> pd.DataFrame:
    dtypes = {
        "station": "string",
        "line": "string",
        "entries_2019": "Int64",
        "entries_2025": "Int64",
        "comparable": "boolean",
    }
    rides = pd.read_csv(path, dtype=dtypes)
    rides["station"] = rides["station"].str.strip()
    rides["line"] = rides["line"].astype("category")
    return rides


def recovery_table(rides: pd.DataFrame, min_base: int = 100_000) -> pd.DataFrame:
    usable = rides.dropna(
        subset=["station", "line", "entries_2019", "entries_2025"]
    ).copy()
    usable = usable[usable["comparable"]]
    usable = usable.query(
        "entries_2019 >= @min_base and entries_2025 > 0"
    )
    usable["recovery"] = 100 * usable["entries_2025"] / usable["entries_2019"]
    return usable.sort_values("recovery").reset_index(drop=True)


def draw_recovery(
    stations: pd.DataFrame,
    line_medians: pd.Series,
    output_path: Path,
) -> None:
    width, height = 1800, 720
    navy, teal, amber = "#202020", "#4C72B0", "#B44A3F"
    grey, grid = "#666666", "#D6D6D6"
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    regular = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)

    draw.text((70, 32), "Station recovery rates", fill=navy, font=bold)
    draw.text((70, 78), "CTA rail entries, 2025 as a share of 2019", fill=grey, font=regular)

    left_x, right_x = 110, 1030
    top_y, base_y = 170, 620
    draw.line((left_x, base_y, left_x + 650, base_y), fill=grey, width=2)
    draw.line((left_x, top_y, left_x, base_y), fill=grey, width=2)

    counts, edges = np.histogram(stations["recovery"], bins=np.arange(30, 131, 10))
    max_count = max(counts)
    bar_width = 650 / len(counts)
    for count, left in zip(counts, edges[:-1]):
        x0 = left_x + (left - 30) / 100 * 650 + 4
        x1 = x0 + bar_width - 8
        y0 = base_y - count / max_count * 330
        draw.rectangle((x0, y0, x1, base_y), fill=teal)
        draw.text(((x0 + x1) / 2, base_y + 12), f"{left:.0f}", anchor="ma", fill=grey, font=regular)

    for value, color, label, offset in (
        (63, amber, "CTA rail: 63%", 0),
        (stations["recovery"].median(), navy, "Station median: 67%", 24),
    ):
        x = left_x + (value - 30) / 100 * 650
        draw.line((x, top_y, x, base_y), fill=color, width=3)
        draw.text((x + 8, top_y + offset), label, fill=color, font=regular)

    draw.text((left_x + 250, 662), "2025 entries / 2019 entries (%)", fill=grey, font=regular)
    draw.text((right_x, 132), "Median recovery by line", fill=navy, font=bold)

    chart_left, chart_right = right_x + 150, right_x + 670
    max_value = max(line_medians.max(), 100)
    row_height = 390 / len(line_medians)
    for index, (line, value) in enumerate(line_medians.items()):
        y = 205 + index * row_height
        x = chart_left + value / max_value * (chart_right - chart_left)
        color = amber if value < 63 else teal
        draw.text((right_x, y - 2), str(line), fill=navy, font=regular)
        draw.rectangle((chart_left, y, x, y + row_height * 0.58), fill=color)
        draw.text((x + 8, y - 2), f"{value:.0f}%", fill=grey, font=regular)

    axis_y = 205 + len(line_medians) * row_height
    draw.line((chart_left, 190, chart_left, axis_y), fill=grey, width=2)
    for tick in (0, 50, 100):
        x = chart_left + tick / max_value * (chart_right - chart_left)
        draw.line((x, 190, x, axis_y), fill=grid, width=1)
        draw.text((x, axis_y + 8), str(tick), anchor="ma", fill=grey, font=regular)
    draw.text((right_x, 662), "Median station recovery (%)", fill=grey, font=regular)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    rides = load_station_recovery(DATA)
    stations = recovery_table(rides)
    line_medians = (
        stations.groupby("line", observed=True)["recovery"].median().sort_values()
    )

    print(f"Analyzed {len(stations)} comparable stations.")
    print(f"Median station recovery: {stations['recovery'].median():.1f}%")
    print("\nLowest-recovery stations:")
    print(stations[["station", "line", "recovery"]].head(8).to_string(index=False))
    print("\nMedian recovery by line:")
    print(line_medians.round(1).to_string())
    draw_recovery(stations, line_medians, FIGURE)
    print(f"\nSaved chart to {FIGURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
