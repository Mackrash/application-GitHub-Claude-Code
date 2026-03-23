"""SAM simulation runner — orchestrates PySAM execution and result collection."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from cli_anything.sam.utils.sam_backend import run_simulation


def simulate_project(project: dict, verbose: bool = False) -> dict:
    """Run a SAM simulation for the given project.

    Args:
        project: Project dict (modified in-place with results).
        verbose: Print progress information.

    Returns:
        Results dict (also stored in project["results"]).
    """
    tech = project.get("technology", "pvwatts")
    fin = project.get("financial", "none")
    name = project.get("name", "unnamed")

    if verbose:
        print(f"  Running {tech} simulation ({fin} financial model)...")

    # Check weather file
    weather_file = project.get("inputs", {}).get("weather_file")
    if not weather_file and tech in ("pvwatts", "pvdetailed", "wind"):
        if verbose:
            print("  Warning: no weather file set — using PySAM defaults")

    t0 = time.time()
    results = run_simulation(project)
    elapsed = time.time() - t0

    results["simulation_time_s"] = round(elapsed, 3)
    results["simulated_at"] = datetime.now(timezone.utc).isoformat()
    results["project_name"] = name

    project["results"] = results
    return results


def batch_simulate(projects: list, verbose: bool = False) -> list:
    """Run simulations for multiple projects.

    Args:
        projects: List of project dicts.
        verbose: Print progress.

    Returns:
        List of results dicts.
    """
    all_results = []
    for i, project in enumerate(projects):
        if verbose:
            name = project.get("name", f"project_{i}")
            print(f"  [{i+1}/{len(projects)}] {name}")
        try:
            results = simulate_project(project, verbose=verbose)
            all_results.append({"project": project.get("name"), "status": "ok", "results": results})
        except Exception as e:
            all_results.append({"project": project.get("name"), "status": "error", "error": str(e)})
    return all_results


def check_simulation_ready(project: dict) -> tuple:
    """Check if a project is ready to simulate.

    Returns:
        (ready: bool, issues: list of warning strings)
    """
    issues = []
    tech = project.get("technology", "pvwatts")
    inputs = project.get("inputs", {})

    # Check weather file for energy technologies
    if tech in ("pvwatts", "pvdetailed", "wind"):
        weather_file = inputs.get("weather_file")
        if not weather_file:
            issues.append("No weather file set — PySAM will use internal defaults")
        elif not Path(weather_file).is_file():
            issues.append(f"Weather file not found: {weather_file}")

    # Check capacity
    capacity = inputs.get("system_capacity")
    if capacity is not None and float(capacity) <= 0:
        issues.append(f"Invalid system capacity: {capacity} kW")

    # Check location for pvwatts without weather file
    if tech == "pvwatts" and not inputs.get("weather_file"):
        loc = inputs.get("location", {})
        if not loc.get("lat") or not loc.get("lon"):
            issues.append("Location (lat/lon) required when no weather file is set")

    return len(issues) == 0, issues


def get_simulation_summary(results: dict) -> dict:
    """Extract a human-readable summary from results."""
    summary = {}

    if "annual_energy" in results:
        summary["Annual Energy (kWh)"] = f"{results['annual_energy']:,.1f}"
    if "capacity_factor" in results:
        summary["Capacity Factor (%)"] = f"{results['capacity_factor']:.1f}"
    if "kwh_per_kw" in results:
        summary["kWh/kW"] = f"{results['kwh_per_kw']:.1f}"
    if "dc_annual" in results:
        summary["Annual DC Energy (kWh)"] = f"{results['dc_annual']:,.1f}"
    if "solrad_annual" in results:
        summary["Solar Irradiance (kWh/m²/day)"] = f"{results['solrad_annual']:.2f}"
    if "lcoe_nominal" in results:
        summary["LCOE Nominal ($/kWh)"] = f"{results['lcoe_nominal']:.4f}"
    if "lcoe_real" in results:
        summary["LCOE Real ($/kWh)"] = f"{results['lcoe_real']:.4f}"
    if "payback_period" in results:
        summary["Payback Period (years)"] = f"{results['payback_period']:.1f}"
    if "npv" in results:
        summary["NPV ($)"] = f"{results['npv']:,.0f}"
    if "irr" in results:
        summary["IRR (%)"] = f"{results['irr']:.2f}"
    if "simulation_time_s" in results:
        summary["Simulation Time (s)"] = f"{results['simulation_time_s']:.3f}"

    return summary
