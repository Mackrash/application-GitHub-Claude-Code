---
name: "cli-anything-sam"
description: "CLI harness for NREL System Advisor Model (SAM). Simulate solar PV (PVWatts, detailed), wind, battery storage, and geothermal energy systems with full financial analysis using PySAM. Create projects, set parameters, run simulations, and export results — all from the command line."
triggers:
  - "simulate solar"
  - "pvwatts simulation"
  - "SAM project"
  - "renewable energy simulation"
  - "wind power model"
  - "LCOE calculation"
  - "PySAM"
  - "annual energy production"
  - "solar payback period"
---

# cli-anything-sam Skill

CLI harness for **NREL System Advisor Model (SAM)** using PySAM.

## Installation

```bash
pip install NREL-PySAM          # Required backend
pip install -e /path/to/SAM/agent-harness  # Install CLI
cli-anything-sam --version
```

## Core Workflow

```bash
# 1. Create project
cli-anything-sam project new -n "Denver PV" -t pvwatts -f residential -o project.sam.json

# 2. Configure
cli-anything-sam project set system_capacity 6.0 -o project.sam.json
cli-anything-sam project set location.lat 39.74 -o project.sam.json
cli-anything-sam project set location.lon -104.99 -o project.sam.json

# 3. Set weather file (required for real results)
cli-anything-sam weather set denver.epw -p project.sam.json -o project.sam.json

# 4. Simulate
cli-anything-sam simulate run project.sam.json -o project.sam.json

# 5. View results
cli-anything-sam results show project.sam.json
cli-anything-sam results export project.sam.json -o results.csv -f csv
```

## Technologies

| Value        | Description                   |
|-------------|-------------------------------|
| `pvwatts`   | PVWatts v8 — simple PV        |
| `pvdetailed`| Detailed PV (PVsamv1)         |
| `wind`      | Wind power                    |
| `battery`   | Simple battery storage        |
| `geothermal`| Geothermal power              |

## Financial Models

| Value         | Description                    |
|--------------|--------------------------------|
| `residential` | Residential Owner (net metering)|
| `commercial`  | Commercial Owner               |
| `singleowner` | Single Owner (utility-scale)   |
| `lcoe`        | LCOE Fixed Charge Rate         |
| `none`        | Energy only (no financials)    |

## Command Groups

| Group      | Commands                              |
|-----------|---------------------------------------|
| `project` | new, open, save, info, set, inputs    |
| `simulate`| run, check                            |
| `weather` | set, info, list, create-synthetic     |
| `results` | show, export                          |
| `info`    | Version and PySAM status              |
| `repl`    | Interactive session (default)         |

## Key Parameters (pvwatts)

| Parameter        | Default | Unit   | Description              |
|-----------------|---------|--------|--------------------------|
| system_capacity  | 4.0     | kW     | DC nameplate capacity    |
| tilt             | 20.0    | °      | Panel tilt angle         |
| azimuth          | 180.0   | °      | Panel azimuth (180=south)|
| losses           | 14.08   | %      | System losses            |
| dc_ac_ratio      | 1.2     | —      | DC-to-AC ratio           |
| inv_eff          | 96.0    | %      | Inverter efficiency      |
| location.lat     | 39.74   | °N     | Site latitude            |
| location.lon     | -104.99 | °E     | Site longitude           |

## Key Outputs

| Output          | Description                        |
|----------------|------------------------------------|
| annual_energy   | Annual AC energy (kWh)            |
| capacity_factor | Capacity factor (%)               |
| kwh_per_kw      | Specific yield (kWh/kW/year)      |
| lcoe_nominal    | LCOE nominal ($/kWh)              |
| lcoe_real       | LCOE real ($/kWh)                 |
| payback_period  | Simple payback (years)            |
| npv             | Net present value ($)             |
| irr             | Internal rate of return (%)       |

## JSON Output (Agent Mode)

Use `--json` for all commands:

```bash
# Create project and capture output
cli-anything-sam --json project new -n Test -t pvwatts -f residential -o test.sam.json

# Run simulation
cli-anything-sam --json simulate run test.sam.json

# Get results
cli-anything-sam --json results show test.sam.json
```

JSON response structure:
```json
{
  "status": "ok",
  "results": {
    "annual_energy": 8234.5,
    "capacity_factor": 23.4,
    "lcoe_nominal": 0.078,
    "payback_period": 7.8
  }
}
```

## Weather Files

- **Solar (.epw, .csv):** Download from https://nsrdb.nrel.gov/ (free API key required)
- **Wind (.srw):** Download from NREL Wind Toolkit
- **Synthetic (testing only):**
  ```bash
  cli-anything-sam weather create-synthetic --lat 39.74 --lon -104.99 -o test.csv
  ```

## Error Handling

- **PySAM not installed:** `RuntimeError: NREL-PySAM is not installed. Install: pip install NREL-PySAM`
- **No weather file:** Warning shown, PySAM uses internal defaults (less accurate)
- **Simulation failed:** Full PySAM error message shown

## REPL Mode

```bash
cli-anything-sam           # Starts interactive REPL
sam [Denver PV] ❯ project info
sam [Denver PV] ❯ simulate run
sam [Denver PV] ❯ results show
sam [Denver PV] ❯ undo
sam [Denver PV] ❯ quit
```
