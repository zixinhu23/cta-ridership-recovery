# CTA Rail Ridership Recovery, 2019-2025

This repository contains a short Python analysis of station-level CTA rail
entries and the two-page programming supplement prepared for the University of
Chicago MS in Applied Data Science application.

## Research question

Which CTA rail stations lagged the system's recovery between 2019 and 2025?

The analysis uses annual station entry totals from the CTA Annual Ridership
Reports. After matching stations across the two reports and keeping stations
with at least 100,000 entries in 2019, the final data contain 112 stations.

## Main result

The median station recovery was 66.7% of 2019 entries in 2025. The five most
slowly recovering stations were Oak Park, Pulaski, Racine, Austin, and Forest
Park. All five are on the Blue Line's Forest Park branch.

![CTA rail recovery chart](cta_recovery.png)

## Files

- `supplement_code.py`: analysis code shown in the two-page PDF
- `cta_recovery_analysis.py`: full analysis and chart function
- `cta_station_recovery.csv`: processed station-level analysis data
- [CTA_rail_recovery_programming_supplement.pdf](CTA_rail_recovery_programming_supplement.pdf): final two-page PDF
- `requirements.txt`: Python dependencies

## Data sources

- [CTA Annual Ridership Report, Calendar Year 2019](https://www.transitchicago.com/assets/1/6/2019_Annual_Ridership_Report.pdf)
- [CTA Annual Ridership Report, Calendar Year 2025](https://www.transitchicago.com/assets/1/6/2025_Annual_Ridership_Report.pdf)
- [CTA ridership report index](https://www.transitchicago.com/ridership/)

## Run the analysis

```bash
python -m pip install -r requirements.txt
python supplement_code.py
```

The script reads `cta_station_recovery.csv`, prints the station and line
summaries, and writes `cta_recovery.png`.

## Interpretation limits

- Station entries count boardings, not unique riders.
- Ridership is a usage measure, not a complete measure of accessibility.
- CTA changed its 2025 ridership processing methodology, so the two years are
  not perfectly comparable.
- The results are descriptive and should not be read as causal effects.
