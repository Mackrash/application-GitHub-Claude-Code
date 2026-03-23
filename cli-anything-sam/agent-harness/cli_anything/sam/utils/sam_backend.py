"""PySAM backend — wraps NREL-PySAM with clear errors and a unified interface."""

import shutil
import subprocess
import sys
from pathlib import Path


def find_pysam():
    """Verify PySAM is installed. Returns version string or raises RuntimeError."""
    try:
        import PySAM
        return getattr(PySAM, "__version__", "installed")
    except ImportError:
        raise RuntimeError(
            "NREL-PySAM is not installed.\n"
            "Install it with:\n"
            "  pip install NREL-PySAM\n\n"
            "PySAM documentation: https://nrel-pysam.readthedocs.io/"
        )


# ── Technology module loaders ─────────────────────────────────────────────────

def _load_pvwatts(config_name: str):
    """Load PVWatts v8 technology module."""
    find_pysam()
    import PySAM.Pvwattsv8 as pv
    if config_name:
        try:
            return pv.default(config_name)
        except Exception:
            return pv.new()
    return pv.new()


def _load_pvdetailed(config_name: str):
    """Load detailed PV (PVsamv1) technology module."""
    find_pysam()
    import PySAM.Pvsamv1 as pv
    if config_name:
        try:
            return pv.default(config_name)
        except Exception:
            return pv.new()
    return pv.new()


def _load_wind(config_name: str):
    """Load wind power technology module."""
    find_pysam()
    import PySAM.Windpower as wp
    if config_name:
        try:
            return wp.default(config_name)
        except Exception:
            return wp.new()
    return wp.new()


def _load_battery(config_name: str):
    """Load simple battery module."""
    find_pysam()
    import PySAM.Battwatts as batt
    if config_name:
        try:
            return batt.default(config_name)
        except Exception:
            return batt.new()
    return batt.new()


def _load_geothermal(config_name: str):
    """Load geothermal technology module."""
    find_pysam()
    import PySAM.Geothermal as geo
    if config_name:
        try:
            return geo.default(config_name)
        except Exception:
            return geo.new()
    return geo.new()


_TECH_LOADERS = {
    "pvwatts":    _load_pvwatts,
    "pvdetailed": _load_pvdetailed,
    "wind":       _load_wind,
    "battery":    _load_battery,
    "geothermal": _load_geothermal,
}

# ── Financial module loaders ──────────────────────────────────────────────────

def _load_cashloan(tech_module, config_name: str):
    """Load Cashloan financial module (residential/commercial)."""
    import PySAM.Cashloan as cl
    if config_name:
        try:
            return cl.from_existing(tech_module, config_name)
        except Exception:
            return cl.from_existing(tech_module)
    return cl.from_existing(tech_module)


def _load_singleowner(tech_module, config_name: str):
    """Load SingleOwner financial module (utility-scale)."""
    import PySAM.Singleowner as so
    if config_name:
        try:
            return so.from_existing(tech_module, config_name)
        except Exception:
            return so.from_existing(tech_module)
    return so.from_existing(tech_module)


def _load_lcoefcr(tech_module, config_name: str):
    """Load LCOE Fixed Charge Rate financial module."""
    import PySAM.Lcoefcr as lcoe
    if config_name:
        try:
            return lcoe.from_existing(tech_module, config_name)
        except Exception:
            return lcoe.from_existing(tech_module)
    return lcoe.from_existing(tech_module)


_FIN_LOADERS = {
    "residential": _load_cashloan,
    "commercial":  _load_cashloan,
    "singleowner": _load_singleowner,
    "lcoe":        _load_lcoefcr,
}

# ── Main simulation runner ────────────────────────────────────────────────────

def run_simulation(project: dict) -> dict:
    """Run a SAM simulation using PySAM.

    Args:
        project: Project dict with technology, financial, inputs, financial_inputs.

    Returns:
        Results dict with energy, financial metrics, and raw outputs.

    Raises:
        RuntimeError: If PySAM not installed or simulation fails.
    """
    find_pysam()

    tech = project.get("technology", "pvwatts")
    fin  = project.get("financial", "none")
    config_name = project.get("pysam_config")
    inputs = project.get("inputs", {})
    fin_inputs = project.get("financial_inputs", {})

    if tech not in _TECH_LOADERS:
        raise ValueError(f"Unsupported technology: {tech}")

    # Load technology module
    tech_module = _TECH_LOADERS[tech](config_name)

    # Apply technology inputs
    _apply_tech_inputs(tech_module, tech, inputs)

    # Execute technology simulation
    try:
        tech_module.execute()
    except Exception as e:
        raise RuntimeError(f"PySAM simulation failed ({tech}): {e}") from e

    # Collect technology outputs
    results = _collect_tech_outputs(tech_module, tech)

    # Run financial model if requested
    if fin in _FIN_LOADERS:
        fin_module = _FIN_LOADERS[fin](tech_module, config_name)
        _apply_fin_inputs(fin_module, fin, fin_inputs)
        # Provide full 8760-element hourly generation array to the financial model.
        # Required when solar_resource_data dict was used (pvwatts may not auto-link).
        try:
            ac_hourly = list(tech_module.Outputs.ac)
            if len(ac_hourly) == 8760:
                fin_module.SystemOutput.gen = ac_hourly
        except Exception:
            pass
        try:
            fin_module.execute()
        except Exception as e:
            raise RuntimeError(f"PySAM financial simulation failed ({fin}): {e}") from e
        results.update(_collect_fin_outputs(fin_module, fin))

    return results


def _build_solar_resource_data(loc: dict, avg_ghi: float = 5.5) -> dict:
    """Build a solar_resource_data dict from location + synthetic irradiance.

    This creates a synthetic but valid resource for PySAM when no EPW/TMY file
    is available. For real analysis, always use measured weather data.

    Args:
        loc: Location dict with lat, lon, tz, elev.
        avg_ghi: Average daily GHI in kWh/m²/day (default 5.5 = sunny mid-latitude).

    Returns:
        solar_resource_data dict compatible with PySAM SolarResource.
    """
    import math

    lat  = float(loc.get("lat", 39.74))
    lon  = float(loc.get("lon", -104.99))
    tz   = float(loc.get("tz", -7))
    elev = float(loc.get("elev", 0))

    peak_ghi = avg_ghi * 1000 / 6  # W/m² peak (assuming 6 sun-hours)

    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    year_list, month_list, day_list, hour_list, minute_list = [], [], [], [], []
    ghi_list, dni_list, dhi_list, wspd_list, tdry_list = [], [], [], [], []

    doy = 0
    for mo_idx, days in enumerate(days_per_month):
        for d in range(1, days + 1):
            doy += 1
            # Seasonal temperature variation
            temp = 15.0 + 10 * math.sin(2 * math.pi * (doy - 80) / 365)
            for hr in range(24):
                year_list.append(2020)
                month_list.append(mo_idx + 1)
                day_list.append(d)
                hour_list.append(hr)
                minute_list.append(30)

                # Simple diurnal solar profile
                sun_angle = math.sin(math.pi * (hr - 6) / 12)
                ghi = max(0.0, peak_ghi * sun_angle) if 6 <= hr <= 18 else 0.0
                ghi_list.append(round(ghi))
                dni_list.append(round(ghi * 0.8))
                dhi_list.append(round(ghi * 0.2))
                wspd_list.append(3.0)
                tdry_list.append(round(temp, 1))

    return {
        "lat":    lat,
        "lon":    lon,
        "tz":     tz,
        "elev":   elev,
        "year":   year_list,
        "month":  month_list,
        "day":    day_list,
        "hour":   hour_list,
        "minute": minute_list,
        "dn":     dni_list,    # DNI
        "df":     dhi_list,    # DHI
        "gh":     ghi_list,    # GHI
        "wspd":   wspd_list,
        "tdry":   tdry_list,
    }


def _apply_tech_inputs(module, tech: str, inputs: dict):
    """Apply technology inputs to a PySAM module."""
    loc = inputs.get("location", {})
    weather_file = inputs.get("weather_file")

    # Determine if we have a file PySAM can read natively (EPW, TM2, TM3, SMW)
    # CSV files from create_simple_tmy_csv are NOT in NSRDB format PySAM expects,
    # so we use solar_resource_data dict for those.
    _native_extensions = {".epw", ".tm2", ".tm3", ".smw"}
    _use_file = (
        weather_file
        and Path(weather_file).is_file()
        and Path(weather_file).suffix.lower() in _native_extensions
    )

    if tech == "pvwatts":
        sd = module.SystemDesign
        if "system_capacity" in inputs:
            sd.system_capacity = float(inputs["system_capacity"])
        if "tilt" in inputs:
            sd.tilt = float(inputs["tilt"])
        if "azimuth" in inputs:
            sd.azimuth = float(inputs["azimuth"])
        if "losses" in inputs:
            sd.losses = float(inputs["losses"])
        if "array_type" in inputs:
            sd.array_type = int(inputs["array_type"])
        if "module_type" in inputs:
            sd.module_type = int(inputs["module_type"])
        if "dc_ac_ratio" in inputs:
            sd.dc_ac_ratio = float(inputs["dc_ac_ratio"])
        if "inv_eff" in inputs:
            sd.inv_eff = float(inputs["inv_eff"])
        if "gcr" in inputs:
            sd.gcr = float(inputs["gcr"])

        sr = module.SolarResource
        if _use_file:
            sr.solar_resource_file = weather_file
        else:
            # Use solar_resource_data dict (works with CSV or no weather file)
            sr.solar_resource_data = _build_solar_resource_data(loc)

    elif tech == "pvdetailed":
        if "system_capacity" in inputs:
            try:
                module.SystemDesign.system_capacity = float(inputs["system_capacity"])
            except Exception:
                pass
        sr = module.SolarResource if hasattr(module, "SolarResource") else None
        if sr:
            if _use_file:
                try:
                    sr.solar_resource_file = weather_file
                except Exception:
                    pass
            else:
                try:
                    sr.solar_resource_data = _build_solar_resource_data(loc)
                except Exception:
                    pass

    elif tech == "wind":
        if weather_file and Path(weather_file).is_file() and Path(weather_file).suffix.lower() == ".srw":
            try:
                module.Resource.wind_resource_filename = weather_file
            except Exception:
                pass
        if "system_capacity" in inputs:
            try:
                module.Farm.system_capacity = float(inputs["system_capacity"])
            except Exception:
                pass
        if "hub_height" in inputs:
            try:
                module.Turbine.wind_turbine_hub_ht = float(inputs["hub_height"])
            except Exception:
                pass

    elif tech == "battery":
        for key in ("batt_simple_enable", "batt_simple_kwh", "batt_simple_kw",
                    "batt_simple_chemistry", "batt_simple_dispatch",
                    "batt_simple_meter_position"):
            if key in inputs:
                try:
                    setattr(module.BatterySystem, key, inputs[key])
                except Exception:
                    pass

    elif tech == "geothermal":
        for key in ("resource_depth", "resource_temp", "plant_efficiency_input"):
            if key in inputs:
                try:
                    setattr(module, key, inputs[key])
                except Exception:
                    pass


def _apply_fin_inputs(module, fin: str, fin_inputs: dict):
    """Apply financial inputs to a PySAM financial module."""
    mappings = {
        "analysis_period":       ("FinancialParameters", "analysis_period"),
        "inflation_rate":        ("FinancialParameters", "inflation_rate"),
        "real_discount_rate":    ("FinancialParameters", "real_discount_rate"),
        "total_installed_cost":  ("SystemCosts", "total_installed_cost"),
        "federal_tax_rate":      ("FinancialParameters", "federal_tax_rate"),
        "state_tax_rate":        ("FinancialParameters", "state_tax_rate"),
    }
    for key, value in fin_inputs.items():
        if key in mappings:
            group_name, attr = mappings[key]
            try:
                group = getattr(module, group_name)
                setattr(group, attr, value)
            except Exception:
                pass


def _collect_tech_outputs(module, tech: str) -> dict:
    """Collect key technology outputs from a PySAM module."""
    results = {"technology": tech}
    out = module.Outputs

    try:
        results["annual_energy"] = float(out.ac_annual)
    except Exception:
        pass
    try:
        results["capacity_factor"] = float(out.capacity_factor)
    except Exception:
        pass
    try:
        # Monthly AC energy (list of 12)
        monthly = list(out.ac_monthly)
        results["monthly_energy"] = monthly
    except Exception:
        pass
    try:
        results["kwh_per_kw"] = float(out.kwh_per_kw)
    except Exception:
        pass

    # PVWatts-specific
    if tech == "pvwatts":
        try:
            results["dc_annual"] = float(out.dc_annual)
        except Exception:
            pass
        try:
            results["solrad_annual"] = float(out.solrad_annual)
        except Exception:
            pass

    return results


def _collect_fin_outputs(module, fin: str) -> dict:
    """Collect key financial outputs from a PySAM financial module."""
    results = {"financial": fin}
    out = module.Outputs

    for attr, key in [
        ("lcoe_nom",       "lcoe_nominal"),
        ("lcoe_real",      "lcoe_real"),
        ("payback",        "payback_period"),
        ("discounted_payback", "discounted_payback"),
        ("npv",            "npv"),
        ("irr",            "irr"),
    ]:
        try:
            val = getattr(out, attr)
            if val is not None:
                results[key] = float(val)
        except Exception:
            pass

    return results


def get_pysam_version() -> str:
    """Return installed PySAM version."""
    find_pysam()
    import PySAM
    return getattr(PySAM, "__version__", "unknown")


def list_available_configs(technology: str = None) -> list:
    """List available PySAM default configuration names."""
    from cli_anything.sam.core.project import PYSAM_DEFAULTS
    configs = []
    for (tech, fin), config in PYSAM_DEFAULTS.items():
        if technology is None or tech == technology:
            configs.append({
                "technology": tech,
                "financial":  fin,
                "config":     config,
            })
    return configs
