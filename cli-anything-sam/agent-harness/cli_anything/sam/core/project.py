"""SAM project management — create, open, save, inspect SAM simulation projects."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

SUPPORTED_TECHNOLOGIES = {
    "pvwatts":    "PVWatts v8 (simple residential/commercial PV)",
    "pvdetailed": "Detailed PV (system-level modeling)",
    "wind":       "Wind Power",
    "battery":    "Simple Battery Storage",
    "geothermal": "Geothermal Power",
}

SUPPORTED_FINANCIALS = {
    "none":        "No financial model (energy only)",
    "residential": "Residential Owner (net metering)",
    "commercial":  "Commercial Owner",
    "singleowner": "Single Owner (utility-scale)",
    "lcoe":        "LCOE Fixed Charge Rate Calculator",
}

# PySAM .default() config names by (technology, financial)
PYSAM_DEFAULTS = {
    ("pvwatts",    "residential"): "PVWattsResidential",
    ("pvwatts",    "commercial"):  "PVWattsCommercial",
    ("pvwatts",    "singleowner"): "PVWattsSingleOwner",
    ("pvwatts",    "lcoe"):        "PVWattsLCOECalculator",
    ("pvwatts",    "none"):        "PVWattsNone",
    ("pvdetailed", "residential"): "FlatPlatePVResidential",
    ("pvdetailed", "commercial"):  "FlatPlatePVCommercial",
    ("pvdetailed", "singleowner"): "FlatPlatePVSingleOwner",
    ("wind",       "singleowner"): "WindPowerSingleOwner",
    ("wind",       "commercial"):  "WindPowerCommercial",
    ("wind",       "none"):        "WindPowerNone",
    ("geothermal", "singleowner"): "GeothermalPowerSingleOwner",
}

# Default technology inputs
_DEFAULT_INPUTS = {
    "pvwatts": {
        "system_capacity": 4.0,
        "module_type":     0,       # 0=Standard, 1=Premium, 2=Thin film
        "losses":          14.08,   # %
        "array_type":      1,       # 1=Fixed Open Rack
        "tilt":            20.0,    # degrees
        "azimuth":         180.0,   # degrees (south)
        "dc_ac_ratio":     1.2,
        "inv_eff":         96.0,    # %
        "gcr":             0.4,
        "location": {
            "lat":  39.7392,
            "lon":  -104.9903,
            "elev": 1611,
            "tz":   -7,
        },
        "weather_file": None,
    },
    "pvdetailed": {
        "system_capacity":    10.0,
        "modules_per_string": 10,
        "strings_in_parallel": 2,
        "inverter_count":     1,
        "tilt":               20.0,
        "azimuth":            180.0,
        "losses":             14.08,
        "location": {
            "lat":  39.7392,
            "lon":  -104.9903,
            "elev": 1611,
            "tz":   -7,
        },
        "weather_file": None,
    },
    "wind": {
        "system_capacity":     1500.0,   # kW total
        "num_turbines":        10,
        "turbine_kw_siting":   150.0,    # kW per turbine
        "hub_height":          80.0,     # m
        "location": {
            "lat": 39.7392,
            "lon": -104.9903,
        },
        "weather_file": None,
    },
    "battery": {
        "batt_simple_enable":          1,
        "batt_simple_kwh":             10.0,
        "batt_simple_kw":              5.0,
        "batt_simple_chemistry":       1,   # 1=Li-ion
        "batt_simple_dispatch":        0,   # 0=peak shaving
        "batt_simple_meter_position":  0,   # 0=behind meter
    },
    "geothermal": {
        "system_capacity":      1000.0,   # kW
        "resource_depth":       2000,     # m
        "resource_temp":        200.0,    # °C
        "plant_efficiency_input": 10.0,   # %
        "location": {
            "lat": 39.7392,
            "lon": -104.9903,
        },
    },
}

# Default financial inputs
_DEFAULT_FINANCIAL_INPUTS = {
    "residential": {
        "analysis_period":       25,
        "inflation_rate":        2.5,
        "real_discount_rate":    5.0,
        "total_installed_cost":  12000.0,   # $
        "federal_tax_rate":      22.0,      # %
        "state_tax_rate":        5.0,       # %
        "property_tax_rate":     0.0,       # %
        "loan_option":           1,         # 1=Standard loan
        "loan_term":             25,
        "loan_rate":             3.0,       # %
        "down_payment_fraction": 0.2,
    },
    "commercial": {
        "analysis_period":       25,
        "inflation_rate":        2.5,
        "real_discount_rate":    8.0,
        "total_installed_cost":  30000.0,
        "federal_tax_rate":      21.0,
        "state_tax_rate":        5.0,
        "property_tax_rate":     1.0,
    },
    "singleowner": {
        "analysis_period":       30,
        "inflation_rate":        2.5,
        "real_discount_rate":    7.0,
        "total_installed_cost":  1000000.0,
        "federal_tax_rate":      21.0,
        "state_tax_rate":        5.0,
    },
    "lcoe": {
        "analysis_period":         25,
        "inflation_rate":          2.5,
        "real_discount_rate":      8.0,
        "capital_cost":            1000000.0,
        "fixed_operating_cost":    10000.0,
        "variable_operating_cost": 0.0,
    },
    "none": {},
}


def create_project(
    name: str,
    technology: str = "pvwatts",
    financial: str = "residential",
    output_path: str = None,
    location: dict = None,
    capacity_kw: float = None,
) -> dict:
    """Create a new SAM simulation project.

    Args:
        name: Human-readable project name.
        technology: Technology type (pvwatts, pvdetailed, wind, battery, geothermal).
        financial: Financial model (residential, commercial, singleowner, lcoe, none).
        output_path: If given, save the project to this path.
        location: Override default location {"lat": ..., "lon": ..., "elev": ..., "tz": ...}.
        capacity_kw: Override default system capacity (kW).

    Returns:
        Project dict.
    """
    technology = technology.lower()
    financial = financial.lower()

    if technology not in SUPPORTED_TECHNOLOGIES:
        raise ValueError(
            f"Unknown technology '{technology}'. "
            f"Supported: {', '.join(SUPPORTED_TECHNOLOGIES)}"
        )
    if financial not in SUPPORTED_FINANCIALS:
        raise ValueError(
            f"Unknown financial model '{financial}'. "
            f"Supported: {', '.join(SUPPORTED_FINANCIALS)}"
        )

    import copy
    inputs = copy.deepcopy(_DEFAULT_INPUTS.get(technology, {}))

    if location:
        if "location" in inputs:
            inputs["location"].update(location)
        else:
            inputs["location"] = location

    if capacity_kw is not None:
        inputs["system_capacity"] = float(capacity_kw)

    now = datetime.now(timezone.utc).isoformat()
    project = {
        "name":           name,
        "version":        "1.0.0",
        "technology":     technology,
        "financial":      financial,
        "pysam_config":   PYSAM_DEFAULTS.get((technology, financial)),
        "created_at":     now,
        "modified_at":    now,
        "inputs":         inputs,
        "financial_inputs": copy.deepcopy(_DEFAULT_FINANCIAL_INPUTS.get(financial, {})),
        "results":        None,
    }

    if output_path:
        save_project(project, output_path)

    return project


def open_project(path: str) -> dict:
    """Load a SAM project from a JSON file.

    Args:
        path: Path to .sam.json or .json project file.

    Returns:
        Project dict.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is invalid.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Project file not found: {path}")
    with open(path) as f:
        project = json.load(f)
    _validate_project(project)
    return project


def save_project(project: dict, path: str) -> str:
    """Save a SAM project to a JSON file with exclusive locking.

    Args:
        project: Project dict.
        path: Output file path.

    Returns:
        Absolute path of saved file.
    """
    path = Path(path)
    if not path.suffix:
        path = path.with_suffix(".sam.json")
    path.parent.mkdir(parents=True, exist_ok=True)

    project["modified_at"] = datetime.now(timezone.utc).isoformat()

    try:
        f = open(path, "r+")
    except FileNotFoundError:
        f = open(path, "w")

    with f:
        locked = False
        try:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            locked = True
        except (ImportError, OSError):
            pass
        try:
            f.seek(0)
            f.truncate()
            json.dump(project, f, indent=2)
            f.flush()
        finally:
            if locked:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    return str(path.resolve())


def get_project_info(project: dict) -> dict:
    """Extract a summary dict from a project."""
    tech = project.get("technology", "unknown")
    fin = project.get("financial", "unknown")
    inputs = project.get("inputs", {})
    loc = inputs.get("location", {})
    results = project.get("results")

    info = {
        "name":         project.get("name", "unnamed"),
        "technology":   f"{tech} — {SUPPORTED_TECHNOLOGIES.get(tech, tech)}",
        "financial":    f"{fin} — {SUPPORTED_FINANCIALS.get(fin, fin)}",
        "pysam_config": project.get("pysam_config", "(not set)"),
        "capacity_kw":  str(inputs.get("system_capacity", "?")),
        "location":     f"lat={loc.get('lat','?')}, lon={loc.get('lon','?')}",
        "weather_file": inputs.get("weather_file") or "(not set)",
        "has_results":  "yes" if results else "no",
        "created":      project.get("created_at", "?")[:10],
        "modified":     project.get("modified_at", "?")[:10],
    }

    if results:
        if "annual_energy" in results:
            info["annual_energy_kwh"] = f"{results['annual_energy']:,.1f}"
        if "lcoe_nominal" in results:
            info["lcoe_nominal_$/kwh"] = f"{results['lcoe_nominal']:.4f}"
        if "payback_period" in results:
            info["payback_years"] = f"{results['payback_period']:.1f}"

    return info


def set_input(project: dict, key: str, value) -> dict:
    """Set a technology input parameter.

    Supports dot notation: 'location.lat'
    """
    if "." in key:
        parent, child = key.split(".", 1)
        if parent not in project["inputs"]:
            project["inputs"][parent] = {}
        project["inputs"][parent][child] = value
    else:
        project["inputs"][key] = value
    return project


def set_financial_input(project: dict, key: str, value) -> dict:
    """Set a financial input parameter."""
    project["financial_inputs"][key] = value
    return project


def list_inputs(project: dict) -> dict:
    """Return flattened input dict for display."""
    flat = {}
    inputs = project.get("inputs", {})
    for k, v in inputs.items():
        if isinstance(v, dict):
            for ck, cv in v.items():
                flat[f"{k}.{ck}"] = cv
        else:
            flat[k] = v
    return flat


def _validate_project(project: dict):
    """Validate basic project structure."""
    for key in ("name", "technology", "financial", "inputs"):
        if key not in project:
            raise ValueError(f"Invalid project file: missing required field '{key}'")
    tech = project["technology"]
    if tech not in SUPPORTED_TECHNOLOGIES:
        raise ValueError(f"Unknown technology in project: '{tech}'")
