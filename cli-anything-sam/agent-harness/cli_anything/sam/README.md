# cli-anything-sam

CLI harness for NREL's **System Advisor Model (SAM)** — simulate solar PV, wind, battery storage,
and geothermal projects from the command line using **PySAM**.

## Prerequisites

### 1. Python 3.10+

### 2. PySAM (required — the simulation engine)

```bash
pip install NREL-PySAM
```

PySAM wraps the SAM Simulation Core (SSC). Without it, `cli-anything-sam` will error clearly.

> **Note:** The full SAM GUI application is NOT required. PySAM is the standalone Python SDK.

### 3. Weather data (for energy simulations)

- **Solar projects:** `.epw`, `.csv` (SAM format), or `.tm3` files
  - Free downloads: [NREL NSRDB](https://nsrdb.nrel.gov/) (requires free API key)
  - EPW files: [EnergyPlus Weather](https://energyplus.net/weather)
- **Wind projects:** `.srw` files
  - [NREL Wind Toolkit](https://www.nrel.gov/grid/wind-toolkit.html)

## Installation

```bash
# Clone the repo
git clone https://github.com/...

# Install the CLI
cd SAM/agent-harness
pip install -e .

# Verify
cli-anything-sam --version
cli-anything-sam info
```

## Quick Start

```bash
# Create a PV project
cli-anything-sam project new -n "My Solar" -t pvwatts -f residential -o solar.sam.json

# Set location (Denver, CO)
cli-anything-sam project set location.lat 39.74 -o solar.sam.json
cli-anything-sam project set location.lon -104.99 -o solar.sam.json
cli-anything-sam project set system_capacity 6.0 -o solar.sam.json

# Set a weather file (download from NSRDB first)
cli-anything-sam weather set denver_2020.epw -p solar.sam.json -o solar.sam.json

# Run simulation
cli-anything-sam simulate run solar.sam.json -o solar.sam.json

# View results
cli-anything-sam results show solar.sam.json
cli-anything-sam results export solar.sam.json -o results.csv -f csv
```

## REPL (Interactive Mode)

```bash
cli-anything-sam
```

The REPL provides stateful, interactive access with history, undo/redo, and tab completion.

## Technologies Supported

| Flag         | Technology             | PySAM Module      |
|-------------|------------------------|-------------------|
| `pvwatts`   | PVWatts v8 (simple PV) | `PySAM.Pvwattsv8` |
| `pvdetailed`| Detailed PV            | `PySAM.Pvsamv1`   |
| `wind`      | Wind Power             | `PySAM.Windpower` |
| `battery`   | Simple Battery         | `PySAM.Battwatts` |
| `geothermal`| Geothermal             | `PySAM.Geothermal`|

## Financial Models

| Flag          | Model              | PySAM Module       |
|--------------|--------------------|--------------------|
| `residential` | Residential Owner  | `PySAM.Cashloan`   |
| `commercial`  | Commercial Owner   | `PySAM.Cashloan`   |
| `singleowner` | Single Owner       | `PySAM.Singleowner`|
| `lcoe`        | LCOE Calculator    | `PySAM.Lcoefcr`    |
| `none`        | Energy only        | —                  |

## JSON Output (for AI agents)

All commands support `--json` for machine-readable output:

```bash
cli-anything-sam --json project new -n Test -t pvwatts -f residential -o test.sam.json
cli-anything-sam --json simulate run test.sam.json
cli-anything-sam --json results show test.sam.json
```

## Running Tests

```bash
cd SAM/agent-harness
pip install pytest
pytest cli_anything/sam/tests/ -v -s
```

Force-installed mode (CI):
```bash
CLI_ANYTHING_FORCE_INSTALLED=1 pytest cli_anything/sam/tests/ -v -s
```

## Project File Format

Projects are stored as JSON (`.sam.json`):

```json
{
  "name": "My Solar Project",
  "technology": "pvwatts",
  "financial": "residential",
  "pysam_config": "PVWattsResidential",
  "inputs": {
    "system_capacity": 6.0,
    "tilt": 20.0,
    "azimuth": 180.0,
    "losses": 14.08,
    "location": {"lat": 39.74, "lon": -104.99, "elev": 1611, "tz": -7},
    "weather_file": "/path/to/weather.epw"
  },
  "financial_inputs": {
    "total_installed_cost": 18000,
    "analysis_period": 25
  },
  "results": {
    "annual_energy": 8400.0,
    "lcoe_nominal": 0.078,
    "payback_period": 7.8
  }
}
```

## NREL API Key

For weather downloads from NSRDB or Wind Toolkit:
1. Register at https://developer.nrel.gov/signup/
2. Use the key with the weather fetch commands
