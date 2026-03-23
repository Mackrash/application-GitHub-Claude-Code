# SAM (System Advisor Model) — CLI Harness SOP

## Software Overview

**SAM** (System Advisor Model) is NREL's open-source simulation platform for renewable energy
systems. It models PV, wind, battery storage, geothermal, and more, with full financial analysis.

## Backend Engine

**PySAM** (`NREL-PySAM`) is the official Python wrapper around the SSC (SAM Simulation Core).
It is the CLI backend — no need to build the full C++ SAM application.

```bash
pip install NREL-PySAM
```

## Technology → PySAM Module Mapping

| Technology   | PySAM Module         | Description                        |
|-------------|---------------------|------------------------------------|
| pvwatts      | `PySAM.Pvwattsv8`   | Simple PV (residential/commercial) |
| pvdetailed   | `PySAM.Pvsamv1`     | Detailed PV system modeling        |
| wind         | `PySAM.Windpower`   | Wind power plant                   |
| battery      | `PySAM.Battwatts`   | Simple battery storage             |
| geothermal   | `PySAM.Geothermal`  | Geothermal power plant             |

## Financial → PySAM Module Mapping

| Financial    | PySAM Module         | Description                        |
|-------------|---------------------|------------------------------------|
| residential  | `PySAM.Cashloan`    | Net metering, residential owner    |
| commercial   | `PySAM.Cashloan`    | Commercial owner                   |
| singleowner  | `PySAM.Singleowner` | Utility-scale single owner         |
| lcoe         | `PySAM.Lcoefcr`     | LCOE fixed charge rate calculator  |
| none         | —                   | No financial model                 |

## Default Configuration Names (PySAM `.default()`)

| Technology + Financial | Config Name               |
|-----------------------|---------------------------|
| pvwatts + residential | `PVWattsResidential`      |
| pvwatts + commercial  | `PVWattsCommercial`       |
| pvwatts + singleowner | `PVWattsSingleOwner`      |
| pvwatts + lcoe        | `PVWattsLCOECalculator`   |
| pvdetailed + res      | `FlatPlatePVResidential`  |
| pvdetailed + comm     | `FlatPlatePVCommercial`   |
| pvdetailed + single   | `FlatPlatePVSingleOwner`  |
| wind + singleowner    | `WindPowerSingleOwner`    |

## Simulation Pipeline

```
create_project()               → .sam.json project file
  ↓
set_weather() / fetch_weather() → weather file path in project
  ↓
run_simulation()               → calls PySAM modules
  ↓
collect_results()              → stores results in project JSON
  ↓
export_results()               → CSV / JSON / summary report
```

## Project File Format

Projects are stored as `.sam.json` files:
```json
{
  "name": "my_pv_project",
  "technology": "pvwatts",
  "financial": "residential",
  "pysam_config": "PVWattsResidential",
  "inputs": {
    "system_capacity": 4.0,
    "tilt": 20.0,
    "azimuth": 180.0,
    "losses": 14.08,
    "location": {"lat": 39.74, "lon": -104.99, "elev": 1611, "tz": -7},
    "weather_file": "/path/to/weather.epw"
  },
  "financial_inputs": {
    "total_installed_cost": 12000,
    "analysis_period": 25
  },
  "results": {
    "annual_energy": 6234.5,
    "lcoe_nominal": 0.082,
    "payback_period": 8.2
  }
}
```

## Weather Data Sources

- **NSRDB** (solar): `PySAM.ResourceTools.SRRPResourceDownloader` — requires NREL API key
- **WTK** (wind): `PySAM.ResourceTools.WindResourceDownloader`
- **Local files**: `.epw`, `.srw`, `.csv` (SAM weather format)
- **NREL API key**: https://developer.nrel.gov/signup/

## Key PySAM Patterns

```python
import PySAM.Pvwattsv8 as pv
import PySAM.Cashloan as cl

# Create with defaults
pv_model = pv.default('PVWattsResidential')
cl_model = cl.from_existing(pv_model, 'PVWattsResidential')

# Set inputs
pv_model.SystemDesign.system_capacity = 4.0
pv_model.SolarResource.solar_resource_file = "/path/to/weather.epw"

# Run
pv_model.execute()
cl_model.execute()

# Get outputs
print(pv_model.Outputs.ac_annual)
print(cl_model.Outputs.lcoe_nom)
```

## CLI Command Groups

| Group     | Purpose                                         |
|----------|-------------------------------------------------|
| `project` | Create, open, save, info, list projects         |
| `simulate`| Run PySAM simulations                           |
| `weather` | Fetch/set weather resource files                |
| `results` | Show, export, compare simulation results        |
| `config`  | Set/get technology and financial parameters     |
| `repl`    | Interactive REPL mode                           |
