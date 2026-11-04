# https://github.com/zixinhu23/cta-ridership-recovery
from pathlib import Path

import pandas as pd

from cta_recovery_analysis import draw_recovery


# Station totals compiled from CTA's annual ridership reports.
DATA = Path("cta_station_recovery.csv")
FIGURE = Path("cta_recovery.png")


def load_rides(path):
    types = {
        "station": "string",
        "line": "string",
        "entries_2019": "Int64",
        "entries_2025": "Int64",
        "comparable": "boolean",
    }
    rides = pd.read_csv(path, dtype=types)
    rides["station"] = rides["station"].str.strip()
    rides["line"] = rides["line"].astype("category")
    return rides


def recovery_table(rides, min_base=100_000):
    rides = rides.dropna(subset=["station", "line", "entries_2019", "entries_2025"])
    rides = rides[rides["comparable"]]
    rides = rides[(rides["entries_2019"] >= min_base) & (rides["entries_2025"] > 0)]
    rides["recovery"] = 100 * rides["entries_2025"] / rides["entries_2019"]
    return rides.sort_values("recovery").reset_index(drop=True)


def line_profile(stations):
    return stations.groupby("line", observed=True)["recovery"].median().sort_values()


rides = load_rides(DATA)
stations = recovery_table(rides)
line_medians = line_profile(stations)
slowest = stations.nsmallest(5, "recovery")

print(f"Comparable stations: {len(stations)}")
print(f"Median recovery: {stations['recovery'].median():.1f}%")
print("\nSlowest stations:")
print(slowest[["station", "line", "recovery"]].to_string(index=False))
print("\nMedian recovery by line:")
print(line_medians.round(1).to_string())

draw_recovery(stations, line_medians, FIGURE)
