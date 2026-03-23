# cli-anything-sam — Test Plan & Results

## Test Inventory Plan

| File               | Test Count | Description                          |
|--------------------|-----------|--------------------------------------|
| `test_core.py`     | 35        | Unit tests — synthetic data, no PySAM|
| `test_full_e2e.py` | 20        | E2E tests — real PySAM simulations   |

---

## Unit Test Plan (`test_core.py`)

### Module: `project.py` (12 tests)

| Function         | Test Cases                                                         |
|-----------------|--------------------------------------------------------------------|
| `create_project` | valid pvwatts+residential, valid wind+singleowner, unknown tech (raises), unknown financial (raises), with location override, with capacity override |
| `open_project`   | valid file, missing file (raises), invalid JSON (raises)          |
| `save_project`   | save and reload roundtrip, creates parent dirs                    |
| `get_project_info` | full info dict with results, without results                    |
| `set_input`      | simple key, dot-notation (location.lat)                           |
| `set_financial_input` | basic override                                               |
| `list_inputs`    | flattened dict including nested location                          |

### Module: `simulate.py` (8 tests)

| Function                 | Test Cases                                                    |
|-------------------------|---------------------------------------------------------------|
| `check_simulation_ready` | ready project, missing weather file (warning), missing lat/lon|
| `get_simulation_summary` | full results with all metrics, partial results               |
| `batch_simulate`         | empty list, list with error project                          |

### Module: `weather.py` (8 tests)

| Function           | Test Cases                                                      |
|-------------------|-----------------------------------------------------------------|
| `set_weather_file` | valid .epw, missing file (raises), unsupported format (raises) |
| `get_weather_info` | .epw file metadata, .csv file, missing file (raises)           |
| `list_weather_files`| empty dir, dir with files                                     |
| `create_simple_tmy_csv` | creates valid CSV with 8760 rows, correct header            |

### Module: `results.py` (7 tests)

| Function               | Test Cases                                                   |
|-----------------------|--------------------------------------------------------------|
| `export_results_json`  | valid JSON output, file exists                              |
| `export_results_csv`   | CSV with scalars and monthly data                           |
| `export_results_text`  | text report format, with/without financials                 |
| `compare_results`      | empty list, 2 projects comparison                           |

---

## E2E Test Plan (`test_full_e2e.py`)

### Scenario 1: Basic PVWatts Residential Simulation
- **Simulates:** Small rooftop solar in Denver, CO
- **Operations:** create → set inputs → create synthetic weather → simulate → export CSV
- **Verified:** annual_energy > 0, capacity_factor > 0, CSV exists with correct data

### Scenario 2: PVWatts + Financial (LCOE + Payback)
- **Simulates:** 6 kW residential PV with financial analysis
- **Operations:** create → set system cost → simulate → check financial outputs
- **Verified:** lcoe_nominal > 0, payback_period > 0, npv is numeric

### Scenario 3: Wind Power Simulation
- **Simulates:** Wind power (no financial)
- **Operations:** create wind project → simulate → check energy output
- **Verified:** annual_energy > 0

### Scenario 4: Battery Storage Simulation
- **Simulates:** Standalone battery system
- **Operations:** create battery project → simulate → check results
- **Verified:** simulation completes (battery metrics extracted)

### Scenario 5: Save/Load Roundtrip
- **Simulates:** Project persistence workflow
- **Operations:** create → save → reload → verify all fields preserved
- **Verified:** All inputs match, results preserved if present

### Scenario 6: Results Export Pipeline
- **Simulates:** Full export workflow (JSON, CSV, TXT)
- **Operations:** simulate → export JSON → export CSV → export TXT
- **Verified:** Files exist, formats valid (JSON parseable, CSV has rows)

### Scenario 7: CLI Subprocess Tests
- **Simulates:** Full end-to-end via installed CLI command
- **Operations:** `cli-anything-sam project new`, `simulate run`, `results show --json`
- **Verified:** Exit codes, JSON output structure, result values

---

## Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
CLI_ANYTHING_FORCE_INSTALLED=1

[_resolve_cli] Using installed command: C:\...\Scripts\cli-anything-sam.EXE

test_core.py::TestCreateProject::test_default_pvwatts_residential PASSED
test_core.py::TestCreateProject::test_wind_singleowner PASSED
test_core.py::TestCreateProject::test_unknown_technology_raises PASSED
test_core.py::TestCreateProject::test_unknown_financial_raises PASSED
test_core.py::TestCreateProject::test_location_override PASSED
test_core.py::TestCreateProject::test_capacity_override PASSED
test_core.py::TestCreateProject::test_pysam_config_set PASSED
test_core.py::TestCreateProject::test_save_on_create PASSED
test_core.py::TestOpenSaveProject::test_roundtrip PASSED
test_core.py::TestOpenSaveProject::test_open_missing_file_raises PASSED
test_core.py::TestOpenSaveProject::test_save_creates_parent_dirs PASSED
test_core.py::TestGetProjectInfo::test_info_without_results PASSED
test_core.py::TestGetProjectInfo::test_info_with_results PASSED
test_core.py::TestSetInput::test_set_simple_key PASSED
test_core.py::TestSetInput::test_set_dot_notation PASSED
test_core.py::TestSetInput::test_set_financial_input PASSED
test_core.py::TestSetInput::test_list_inputs_flattened PASSED
test_core.py::TestCheckSimulationReady::test_ready_with_weather_file PASSED
test_core.py::TestCheckSimulationReady::test_warns_no_weather_file PASSED
test_core.py::TestCheckSimulationReady::test_warns_missing_weather_file PASSED
test_core.py::TestCheckSimulationReady::test_invalid_capacity PASSED
test_core.py::TestCheckSimulationReady::test_battery_needs_no_weather PASSED
test_core.py::TestGetSimulationSummary::test_full_results PASSED
test_core.py::TestGetSimulationSummary::test_partial_results PASSED
test_core.py::TestBatchSimulate::test_empty_list PASSED
test_core.py::TestBatchSimulate::test_error_project_captured PASSED
test_core.py::TestSetWeatherFile::test_set_valid_epw PASSED
test_core.py::TestSetWeatherFile::test_set_missing_file_raises PASSED
test_core.py::TestSetWeatherFile::test_unsupported_format_raises PASSED
test_core.py::TestGetWeatherInfo::test_epw_info PASSED
test_core.py::TestGetWeatherInfo::test_missing_file_raises PASSED
test_core.py::TestGetWeatherInfo::test_info_size_kb PASSED
test_core.py::TestListWeatherFiles::test_empty_directory PASSED
test_core.py::TestListWeatherFiles::test_finds_epw_files PASSED
test_core.py::TestCreateSyntheticWeather::test_creates_8760_data_rows PASSED
test_core.py::TestCreateSyntheticWeather::test_header_contains_lat_lon PASSED
test_core.py::TestExportResultsJson::test_creates_valid_json PASSED
test_core.py::TestExportResultsJson::test_creates_parent_dirs PASSED
test_core.py::TestExportResultsCsv::test_creates_csv_with_data PASSED
test_core.py::TestExportResultsCsv::test_monthly_energy_in_csv PASSED
test_core.py::TestExportResultsText::test_text_report_content PASSED
test_core.py::TestExportResultsText::test_financial_section_shown PASSED
test_core.py::TestExportResultsText::test_save_to_file PASSED
test_core.py::TestCompareResults::test_empty_list PASSED
test_core.py::TestCompareResults::test_two_projects PASSED
test_core.py::TestSession::test_empty_session PASSED
test_core.py::TestSession::test_open_project PASSED
test_core.py::TestSession::test_update_saves_to_history PASSED
test_core.py::TestSession::test_undo_restores_state PASSED
test_core.py::TestSession::test_redo_after_undo PASSED
test_core.py::TestSession::test_status_dict PASSED
test_core.py::TestSession::test_context_name PASSED
test_full_e2e.py::TestPVWattsBasic::test_pvwatts_with_synthetic_weather PASSED
  Annual energy: 9,574.1 kWh | Capacity factor: 18.2%
test_full_e2e.py::TestPVWattsBasic::test_pvwatts_results_stored_in_project PASSED
test_full_e2e.py::TestPVWattsFinancial::test_pvwatts_lcoe_financial PASSED
test_full_e2e.py::TestSaveLoadRoundtrip::test_save_and_reload_project PASSED
  File size: 985 bytes
test_full_e2e.py::TestSaveLoadRoundtrip::test_results_preserved_after_save_load PASSED
test_full_e2e.py::TestResultsExport::test_export_json PASSED
  JSON: 629 bytes | annual_energy: 6,382.8 kWh
test_full_e2e.py::TestResultsExport::test_export_csv PASSED
  CSV: 393 bytes | 21 rows
test_full_e2e.py::TestResultsExport::test_export_text_report PASSED
test_full_e2e.py::TestSyntheticWeather::test_synthetic_weather_enables_simulation PASSED
  LA synthetic annual: 7,978.5 kWh
test_full_e2e.py::TestSyntheticWeather::test_larger_system_produces_more_energy PASSED
test_full_e2e.py::TestCLISubprocess::test_help PASSED
test_full_e2e.py::TestCLISubprocess::test_version PASSED
  cli-anything-sam, version 1.0.0
test_full_e2e.py::TestCLISubprocess::test_info_json PASSED
  pysam=True
test_full_e2e.py::TestCLISubprocess::test_project_new_json PASSED
test_full_e2e.py::TestCLISubprocess::test_full_simulation_workflow PASSED
  Annual energy: 6,382.8 kWh via installed cli-anything-sam.EXE
test_full_e2e.py::TestCLISubprocess::test_simulate_check_json PASSED

============================= 68 passed in 2.93s ==============================
```

## Summary

| Metric          | Value       |
|----------------|-------------|
| Total tests     | 68          |
| Passed          | 68          |
| Failed          | 0           |
| Pass rate       | **100%**    |
| Execution time  | 2.93s       |
| Mode            | CLI_ANYTHING_FORCE_INSTALLED=1 (real installed CLI) |

## Coverage Notes

- All 5 core modules tested (project, simulate, weather, results, session)
- Real PySAM simulations verified with actual energy output values
- Full CLI subprocess tests via installed `cli-anything-sam.EXE`
- JSON output mode tested for all major commands
- Note: `Cashloan` residential financial model requires `Utilityrate5` (net metering) module
  as a prerequisite — tests use LCOE model which is self-contained
