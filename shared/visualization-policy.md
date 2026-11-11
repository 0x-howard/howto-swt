# Visualization Policy

## Offer Return chart

For two to three compared offers, `scripts/budget.py` prints a Mermaid `xychart-beta` line chart: x = average weekly hours, y = final projected surplus (in-US surplus when the exchange rate is unknown). Each offer's hours are held inside its own range, so a guaranteed-hours offer is a flat line. The host keeps the chart, the line legend, and the break-even hours exactly as printed; it does not recompute or reshape data points.

The chart comes with one plain sentence stating which offer leads in which hours range, so the answer stays complete if a host shows the Mermaid block as text.

Single-offer answers do not show the chart. More than three offers still receive a full initial comparison; offer a later choice of two or three only when the user wants the chart.
