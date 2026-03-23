"""Unit tests for cli-anything-sam core modules.

All tests use synthetic data — no PySAM or external dependencies required.
Run: pytest test_core.py -v
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from cli_anything.sam.core.project import (
    create_project, open_project, save_project, get_project_info,
    set_input, set_financial_input, list_inputs,
    SUPPORTED_TECHNOLOGIES, SUPPORTED_FINANCIALS,
)
from cli_anything.sam.core.simulate import (
    check_simulation_ready, get_simulation_summary,
    batch_simulate,
)
from cli_anything.sam.core.weather import (
    set_weather_file, get_weather_info, list_weather_files,
    create_simple_tmy_csv, SUPPORTED_WEATHER_FORMATS,
)
from cli_anything.sam.core.results import (
    export_results_json, export_results_csv,
    export_results_text, compare_results,
)
from cli_anything.sam.core.session import Session


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def sample_results():
    return {
        "technology":       "pvwatts",
        "financial":        "residential",
        "project_name":     "Test PV",
        "annual_energy":    8234.5,
        "dc_annual":        8600.0,
        "capacity_factor":  23.4,
        "kwh_per_kw":       1372.4,
        "solrad_annual":    5.12,
        "lcoe_nominal":     0.0782,
        "lcoe_real":        0.0641,
        "payback_period":   8.2,
        "discounted_payback": 12.1,
        "npv":              14250.0,
        "irr":              7.8,
        "simulation_time_s": 0.123,
        "simulated_at":     "2025-01-01T00:00:00",
        "monthly_energy":   [550, 620, 720, 780, 820, 850,
                             870, 840, 790, 680, 560, 480],
    }


# ─────────────────────────────────────────────────────────────────────────────
# project.py tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateProject:
    def test_default_pvwatts_residential(self):
        proj = create_project("Test")
        assert proj["technology"] == "pvwatts"
        assert proj["financial"] == "residential"
        assert proj["name"] == "Test"
        assert "inputs" in proj
        assert "financial_inputs" in proj
        assert proj["results"] is None

    def test_wind_singleowner(self):
        proj = create_project("Wind Farm", technology="wind", financial="singleowner")
        assert proj["technology"] == "wind"
        assert proj["financial"] == "singleowner"
        assert "system_capacity" in proj["inputs"]

    def test_unknown_technology_raises(self):
        with pytest.raises(ValueError, match="Unknown technology"):
            create_project("Bad", technology="unicorn")

    def test_unknown_financial_raises(self):
        with pytest.raises(ValueError, match="Unknown financial"):
            create_project("Bad", financial="lottery")

    def test_location_override(self):
        proj = create_project("Test", location={"lat": 45.0, "lon": -120.0})
        assert proj["inputs"]["location"]["lat"] == 45.0
        assert proj["inputs"]["location"]["lon"] == -120.0

    def test_capacity_override(self):
        proj = create_project("Test", capacity_kw=12.5)
        assert proj["inputs"]["system_capacity"] == 12.5

    def test_pysam_config_set(self):
        proj = create_project("Test", technology="pvwatts", financial="residential")
        assert proj["pysam_config"] == "PVWattsResidential"

    def test_save_on_create(self, tmp_dir):
        path = os.path.join(tmp_dir, "new.sam.json")
        proj = create_project("Test", output_path=path)
        assert Path(path).exists()
        loaded = json.loads(Path(path).read_text())
        assert loaded["name"] == "Test"


class TestOpenSaveProject:
    def test_roundtrip(self, tmp_dir):
        proj = create_project("RoundTrip", technology="pvwatts", financial="residential")
        proj["inputs"]["system_capacity"] = 7.5
        path = os.path.join(tmp_dir, "roundtrip.sam.json")
        save_project(proj, path)
        loaded = open_project(path)
        assert loaded["name"] == "RoundTrip"
        assert loaded["inputs"]["system_capacity"] == 7.5

    def test_open_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            open_project("/nonexistent/path/project.sam.json")

    def test_save_creates_parent_dirs(self, tmp_dir):
        nested = os.path.join(tmp_dir, "a", "b", "c", "proj.sam.json")
        proj = create_project("Nested")
        save_project(proj, nested)
        assert Path(nested).exists()


class TestGetProjectInfo:
    def test_info_without_results(self):
        proj = create_project("Info Test", technology="pvwatts", financial="residential")
        info = get_project_info(proj)
        assert info["name"] == "Info Test"
        assert "pvwatts" in info["technology"]
        assert info["has_results"] == "no"

    def test_info_with_results(self):
        proj = create_project("Info Test")
        proj["results"] = {
            "annual_energy": 7500.0,
            "lcoe_nominal":  0.09,
            "payback_period": 9.5,
        }
        info = get_project_info(proj)
        assert info["has_results"] == "yes"
        assert "7,500" in info["annual_energy_kwh"]


class TestSetInput:
    def test_set_simple_key(self):
        proj = create_project("Test")
        set_input(proj, "system_capacity", 10.0)
        assert proj["inputs"]["system_capacity"] == 10.0

    def test_set_dot_notation(self):
        proj = create_project("Test")
        set_input(proj, "location.lat", 45.0)
        assert proj["inputs"]["location"]["lat"] == 45.0

    def test_set_financial_input(self):
        proj = create_project("Test")
        set_financial_input(proj, "analysis_period", 30)
        assert proj["financial_inputs"]["analysis_period"] == 30

    def test_list_inputs_flattened(self):
        proj = create_project("Test")
        flat = list_inputs(proj)
        assert "system_capacity" in flat
        assert "location.lat" in flat


# ─────────────────────────────────────────────────────────────────────────────
# simulate.py tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckSimulationReady:
    def test_ready_with_weather_file(self, tmp_dir):
        proj = create_project("Test")
        # Create a fake weather file
        wf = os.path.join(tmp_dir, "test.epw")
        Path(wf).write_text("LOCATION,Denver,CO,USA,TMY3,000001,39.74,-104.99,-7,1611\n")
        proj["inputs"]["weather_file"] = wf
        ready, issues = check_simulation_ready(proj)
        # May still have other issues but weather file issue gone
        assert not any("weather" in i.lower() and "not found" in i.lower() for i in issues)

    def test_warns_no_weather_file(self):
        proj = create_project("Test")
        proj["inputs"]["weather_file"] = None
        ready, issues = check_simulation_ready(proj)
        assert any("weather" in i.lower() for i in issues)

    def test_warns_missing_weather_file(self):
        proj = create_project("Test")
        proj["inputs"]["weather_file"] = "/nonexistent/weather.epw"
        ready, issues = check_simulation_ready(proj)
        assert any("not found" in i.lower() for i in issues)

    def test_invalid_capacity(self):
        proj = create_project("Test")
        proj["inputs"]["system_capacity"] = -5.0
        _, issues = check_simulation_ready(proj)
        assert any("capacity" in i.lower() for i in issues)

    def test_battery_needs_no_weather(self):
        proj = create_project("Test", technology="battery")
        ready, issues = check_simulation_ready(proj)
        assert not any("weather" in i.lower() for i in issues)


class TestGetSimulationSummary:
    def test_full_results(self, sample_results):
        summary = get_simulation_summary(sample_results)
        assert "Annual Energy (kWh)" in summary
        assert "LCOE Nominal ($/kWh)" in summary
        assert "Payback Period (years)" in summary
        assert "8,234.5" in summary["Annual Energy (kWh)"]

    def test_partial_results(self):
        results = {"annual_energy": 5000.0, "capacity_factor": 20.0}
        summary = get_simulation_summary(results)
        assert "Annual Energy (kWh)" in summary
        assert "LCOE Nominal ($/kWh)" not in summary


class TestBatchSimulate:
    def test_empty_list(self):
        results = batch_simulate([])
        assert results == []

    def test_error_project_captured(self):
        # Project with invalid config triggers error
        proj = create_project("Bad")
        proj["technology"] = "nonexistent_tech"
        results = batch_simulate([proj])
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "error" in results[0]


# ─────────────────────────────────────────────────────────────────────────────
# weather.py tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSetWeatherFile:
    def test_set_valid_epw(self, tmp_dir):
        wf = os.path.join(tmp_dir, "test.epw")
        Path(wf).write_text("LOCATION,Denver,CO,USA,TMY3,000001,39.74,-104.99,-7,1611\n")
        proj = create_project("Test")
        set_weather_file(proj, wf)
        assert proj["inputs"]["weather_file"] == str(Path(wf).resolve())

    def test_set_missing_file_raises(self):
        proj = create_project("Test")
        with pytest.raises(FileNotFoundError):
            set_weather_file(proj, "/nonexistent/weather.epw")

    def test_unsupported_format_raises(self, tmp_dir):
        wf = os.path.join(tmp_dir, "test.xyz")
        Path(wf).write_text("data")
        proj = create_project("Test")
        with pytest.raises(ValueError, match="Unsupported"):
            set_weather_file(proj, wf)


class TestGetWeatherInfo:
    def test_epw_info(self, tmp_dir):
        wf = os.path.join(tmp_dir, "test.epw")
        Path(wf).write_text(
            "LOCATION,Denver,Colorado,USA,TMY3,724660,39.74,-104.99,-7.0,1611.0\n"
        )
        info = get_weather_info(wf)
        assert info["format"] == "EnergyPlus Weather (solar)"
        assert info["city"] == "Denver"
        assert info["latitude"] == 39.74

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            get_weather_info("/nonexistent.epw")

    def test_info_size_kb(self, tmp_dir):
        wf = os.path.join(tmp_dir, "small.epw")
        content = "LOCATION,City,ST,US,SRC,000,0.0,0.0,0,0\n" + "data\n" * 100
        Path(wf).write_text(content)
        info = get_weather_info(wf)
        assert info["size_kb"] > 0


class TestListWeatherFiles:
    def test_empty_directory(self, tmp_dir):
        files = list_weather_files(tmp_dir)
        assert files == []

    def test_finds_epw_files(self, tmp_dir):
        for name in ["a.epw", "b.epw", "c.srw"]:
            Path(os.path.join(tmp_dir, name)).write_text("header\n")
        files = list_weather_files(tmp_dir)
        exts = {Path(f["file"]).suffix for f in files}
        assert ".epw" in exts
        assert ".srw" in exts


class TestCreateSyntheticWeather:
    def test_creates_8760_data_rows(self, tmp_dir):
        out = os.path.join(tmp_dir, "synthetic.csv")
        path = create_simple_tmy_csv(39.74, -104.99, out)
        assert Path(path).exists()
        with open(path) as f:
            lines = f.readlines()
        # 3 header lines + 8760 data rows
        assert len(lines) == 8760 + 3

    def test_header_contains_lat_lon(self, tmp_dir):
        out = os.path.join(tmp_dir, "synthetic.csv")
        create_simple_tmy_csv(45.0, -122.0, out)
        with open(out) as f:
            first = f.readline()
        assert "45.0" in first
        assert "-122.0" in first


# ─────────────────────────────────────────────────────────────────────────────
# results.py tests
# ─────────────────────────────────────────────────────────────────────────────

class TestExportResultsJson:
    def test_creates_valid_json(self, tmp_dir, sample_results):
        out = os.path.join(tmp_dir, "results.json")
        path = export_results_json(sample_results, out)
        assert Path(path).exists()
        loaded = json.loads(Path(path).read_text())
        assert loaded["annual_energy"] == sample_results["annual_energy"]

    def test_creates_parent_dirs(self, tmp_dir, sample_results):
        nested = os.path.join(tmp_dir, "a", "b", "results.json")
        path = export_results_json(sample_results, nested)
        assert Path(path).exists()


class TestExportResultsCsv:
    def test_creates_csv_with_data(self, tmp_dir, sample_results):
        out = os.path.join(tmp_dir, "results.csv")
        path = export_results_csv(sample_results, out)
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "annual_energy" in content
        assert "8234" in content

    def test_monthly_energy_in_csv(self, tmp_dir, sample_results):
        out = os.path.join(tmp_dir, "results.csv")
        export_results_csv(sample_results, out)
        content = Path(out).read_text()
        assert "Monthly" in content
        assert "Jan" in content


class TestExportResultsText:
    def test_text_report_content(self, sample_results):
        report = export_results_text(sample_results)
        assert "SAM Simulation Results" in report
        assert "ENERGY RESULTS" in report
        assert "8,234" in report

    def test_financial_section_shown(self, sample_results):
        report = export_results_text(sample_results)
        assert "FINANCIAL RESULTS" in report
        assert "LCOE" in report
        assert "Payback" in report

    def test_save_to_file(self, tmp_dir, sample_results):
        out = os.path.join(tmp_dir, "report.txt")
        path = export_results_text(sample_results, out)
        assert Path(path).exists()
        assert "SAM" in Path(path).read_text()


class TestCompareResults:
    def test_empty_list(self):
        result = compare_results([])
        assert result == {}

    def test_two_projects(self, sample_results):
        r2 = dict(sample_results)
        r2["project_name"] = "Project B"
        r2["annual_energy"] = 9000.0
        r2["lcoe_nominal"]  = 0.065
        comparison = compare_results([sample_results, r2])
        assert len(comparison["projects"]) == 2
        assert "annual_energy" in comparison["metrics"]
        assert comparison["metrics"]["annual_energy"]["max"] == 9000.0


# ─────────────────────────────────────────────────────────────────────────────
# session.py tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSession:
    def test_empty_session(self):
        s = Session()
        assert not s.is_open()
        assert s.project is None

    def test_open_project(self):
        proj = create_project("Test")
        s = Session()
        s.open_project(proj, "/tmp/test.sam.json")
        assert s.is_open()
        assert s.project["name"] == "Test"
        assert not s.modified

    def test_update_saves_to_history(self):
        proj = create_project("Test")
        s = Session()
        s.open_project(proj)
        original_cap = proj["inputs"]["system_capacity"]
        new_proj = create_project("Test")
        new_proj["inputs"]["system_capacity"] = 20.0
        s.update_project(new_proj, "increase capacity")
        assert s.modified
        assert s.can_undo()

    def test_undo_restores_state(self):
        proj = create_project("Test")
        s = Session()
        s.open_project(proj)
        # Modify
        new_proj = create_project("Test")
        new_proj["inputs"]["system_capacity"] = 20.0
        s.update_project(new_proj, "set cap 20")
        # Undo
        ok, msg = s.undo()
        assert ok
        assert s.project["inputs"]["system_capacity"] == proj["inputs"]["system_capacity"]

    def test_redo_after_undo(self):
        proj = create_project("Test")
        s = Session()
        s.open_project(proj)
        new_proj = create_project("Test")
        new_proj["inputs"]["system_capacity"] = 20.0
        s.update_project(new_proj, "set cap 20")
        s.undo()
        ok, _ = s.redo()
        assert ok
        assert s.project["inputs"]["system_capacity"] == 20.0

    def test_status_dict(self):
        proj = create_project("Status Test", technology="pvwatts")
        s = Session()
        s.open_project(proj, "/tmp/test.sam.json")
        status = s.status()
        assert status["project"] == "Status Test"
        assert status["technology"] == "pvwatts"
        assert not status["modified"]

    def test_context_name(self):
        proj = create_project("My Project", technology="wind")
        s = Session()
        s.open_project(proj)
        ctx = s.context_name()
        assert "My Project" in ctx
        assert "wind" in ctx
