"""SAM results processing — display, export, and compare simulation results."""

import csv
import json
import os
from pathlib import Path


def export_results_json(results: dict, output_path: str, pretty: bool = True) -> str:
    """Export results to a JSON file.

    Args:
        results: Results dict from simulation.
        output_path: Output file path.
        pretty: If True, pretty-print JSON.

    Returns:
        Absolute path of saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2 if pretty else None)
    return str(path.resolve())


def export_results_csv(results: dict, output_path: str) -> str:
    """Export results to CSV.

    Scalar values go to the main table; monthly arrays to a second sheet-style block.

    Args:
        results: Results dict.
        output_path: Output file path.

    Returns:
        Absolute path of saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)

        # Scalar results
        writer.writerow(["Metric", "Value", "Unit"])
        scalar_units = {
            "annual_energy":      "kWh",
            "dc_annual":          "kWh",
            "capacity_factor":    "%",
            "kwh_per_kw":         "kWh/kW",
            "solrad_annual":      "kWh/m²/day",
            "lcoe_nominal":       "$/kWh",
            "lcoe_real":          "$/kWh",
            "payback_period":     "years",
            "discounted_payback": "years",
            "npv":                "$",
            "irr":                "%",
            "simulation_time_s":  "s",
        }
        for key, unit in scalar_units.items():
            if key in results:
                writer.writerow([key, results[key], unit])

        # Monthly energy
        if "monthly_energy" in results and results["monthly_energy"]:
            writer.writerow([])
            writer.writerow(["Monthly AC Energy (kWh)"])
            writer.writerow(["Month", "Energy (kWh)"])
            monthly = results["monthly_energy"]
            for i, val in enumerate(monthly[:12]):
                month = MONTHS[i] if i < len(MONTHS) else f"Month {i+1}"
                writer.writerow([month, round(val, 2)])

    return str(path.resolve())


def export_results_text(results: dict, output_path: str = None) -> str:
    """Format results as a human-readable text report.

    Args:
        results: Results dict.
        output_path: If given, save to file. Otherwise return as string.

    Returns:
        Report text (or file path if output_path given).
    """
    lines = []
    lines.append("=" * 60)
    lines.append("  SAM Simulation Results")
    lines.append("=" * 60)

    if "project_name" in results:
        lines.append(f"  Project : {results['project_name']}")
    if "technology" in results:
        lines.append(f"  Technology: {results['technology']}")
    if "financial" in results:
        lines.append(f"  Financial : {results['financial']}")
    if "simulated_at" in results:
        lines.append(f"  Simulated : {results['simulated_at'][:19]}")
    lines.append("")

    # Energy results
    lines.append("  ENERGY RESULTS")
    lines.append("  " + "-" * 40)
    for key, label, unit in [
        ("annual_energy",   "Annual AC Energy",       "kWh"),
        ("dc_annual",       "Annual DC Energy",        "kWh"),
        ("capacity_factor", "Capacity Factor",         "%"),
        ("kwh_per_kw",      "Specific Yield",          "kWh/kW"),
        ("solrad_annual",   "Avg Irradiance",          "kWh/m²/day"),
    ]:
        if key in results:
            val = results[key]
            if isinstance(val, float):
                lines.append(f"  {label:<28} {val:>12,.2f}  {unit}")
            else:
                lines.append(f"  {label:<28} {val!s:>12}  {unit}")

    # Monthly energy table
    if "monthly_energy" in results and results["monthly_energy"]:
        MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        lines.append("")
        lines.append("  MONTHLY ENERGY (kWh)")
        lines.append("  " + "-" * 40)
        monthly = results["monthly_energy"][:12]
        for i in range(0, len(monthly), 4):
            row = monthly[i:i+4]
            month_labels = "  ".join(f"{MONTHS[i+j]:<4}" for j in range(len(row)))
            values = "  ".join(f"{v:>7,.0f}" for v in row)
            lines.append(f"  {month_labels}")
            lines.append(f"  {values}")
            lines.append("")

    # Financial results
    fin_keys = ["lcoe_nominal", "lcoe_real", "payback_period",
                "discounted_payback", "npv", "irr"]
    if any(k in results for k in fin_keys):
        lines.append("  FINANCIAL RESULTS")
        lines.append("  " + "-" * 40)
        for key, label, unit in [
            ("lcoe_nominal",       "LCOE (nominal)",       "$/kWh"),
            ("lcoe_real",          "LCOE (real)",           "$/kWh"),
            ("payback_period",     "Payback Period",        "years"),
            ("discounted_payback", "Discounted Payback",    "years"),
            ("npv",                "Net Present Value",     "$"),
            ("irr",                "Internal Rate of Return", "%"),
        ]:
            if key in results:
                val = results[key]
                if isinstance(val, float):
                    fmt = f"{val:>12,.4f}" if "lcoe" in key else f"{val:>12,.2f}"
                    lines.append(f"  {label:<28} {fmt}  {unit}")

    lines.append("")
    lines.append("=" * 60)

    report = "\n".join(lines)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report)
        return str(path.resolve())

    return report


def compare_results(results_list: list) -> dict:
    """Compare results from multiple simulations.

    Args:
        results_list: List of results dicts.

    Returns:
        Comparison dict with per-metric tables.
    """
    if not results_list:
        return {}

    metrics = [
        "annual_energy", "capacity_factor", "kwh_per_kw",
        "lcoe_nominal", "lcoe_real", "payback_period", "npv", "irr",
    ]

    comparison = {"projects": [], "metrics": {}}
    for r in results_list:
        comparison["projects"].append(r.get("project_name", "?"))

    for metric in metrics:
        values = []
        for r in results_list:
            if metric in r:
                values.append(r[metric])
            else:
                values.append(None)

        if any(v is not None for v in values):
            comparison["metrics"][metric] = {
                "values": values,
                "min":    min(v for v in values if v is not None),
                "max":    max(v for v in values if v is not None),
                "best":   comparison["projects"][
                    values.index(min(v for v in values if v is not None))
                    if metric in ("lcoe_nominal", "lcoe_real", "payback_period")
                    else values.index(max(v for v in values if v is not None))
                ],
            }

    return comparison
