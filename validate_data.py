from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent


def load_csv(name: str) -> pd.DataFrame:
    path = ROOT / name
    assert path.exists(), f"Missing file: {name}"
    return pd.read_csv(path)


def station_keys(frame: pd.DataFrame) -> set[tuple[str, str]]:
    return set(zip(frame["station"], frame["line"]))


def main() -> None:
    annual_2019 = load_csv("cta_station_entries_2019.csv")
    annual_2025 = load_csv("cta_station_entries_2025.csv")
    recovery = load_csv("cta_station_recovery.csv")

    assert len(annual_2019) == 142, len(annual_2019)
    assert len(annual_2025) == 142, len(annual_2025)
    assert len(recovery) == 140, len(recovery)

    assert not annual_2019[["station", "line"]].isna().any().any()
    assert not annual_2025[["station", "line"]].isna().any().any()
    assert not recovery[["station", "line"]].isna().any().any()

    assert not annual_2019.duplicated(["station", "line"]).any()
    assert not annual_2025.duplicated(["station", "line"]).any()
    assert not recovery.duplicated(["station", "line"]).any()

    keys_2019 = station_keys(annual_2019)
    keys_2025 = station_keys(annual_2025)
    matched = keys_2019 & keys_2025

    assert len(matched) == 141, len(matched)
    assert keys_2019 - keys_2025 == {("Kildare", "Pink")}
    assert keys_2025 - keys_2019 == {("Damen", "Green")}

    eligible = {
        (row.station, row.line)
        for row in annual_2019.itertuples(index=False)
        if row.entries_2019 >= 100_000
    }
    assert matched - eligible == {("Kostner", "Pink")}
    assert station_keys(recovery) == matched & eligible

    assert recovery["comparable"].notna().all()
    assert recovery["comparable"].sum() == 138
    excluded = set(recovery.loc[~recovery["comparable"], "station"])
    assert excluded == {"Berwyn", "Lawrence"}
    assert (recovery.loc[~recovery["comparable"], "analysis_note"] != "").all()
    assert (recovery.loc[recovery["comparable"], "analysis_note"].isna()).all()

    expected_recovery = (
        recovery["entries_2025"] / recovery["entries_2019"] * 100
    )
    assert expected_recovery.sub(recovery["recovery_pct"]).abs().max() < 1e-9
    assert (recovery["entries_2019"] >= 100_000).all()

    comparable_recovery = recovery.loc[recovery["comparable"], "recovery_pct"]
    median_recovery = comparable_recovery.median()
    assert round(median_recovery, 1) == 66.2

    print("PASS 2019 station totals: 142")
    print("PASS 2025 station totals: 142")
    print("PASS matched station-line pairs: 141")
    print("PASS after 2019 base threshold: 140")
    print("PASS comparable stations: 138")
    print("PASS excluded stations: Berwyn, Lawrence")
    print(f"PASS median recovery: {median_recovery:.1f}%")


if __name__ == "__main__":
    main()
