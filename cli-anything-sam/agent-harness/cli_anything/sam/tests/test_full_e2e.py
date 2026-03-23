"""End-to-end tests for cli-anything-sam.

Tests the full pipeline: project creation → simulation (real PySAM) → results export.

Prerequisites:
  pip install NREL-PySAM

Run:
  pytest test_full_e2e.py -v -s

Force-installed mode (CI):
  CLI_ANYTHING_FORCE_INSTALLED=1 pytest test_full_e2e.py -v -s
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from cli_anything.sam.core.project import create_project, save_project, open_project
from cli_anything.sam.core.simulate import simulate_project, check_simulation_ready
from cli_anything.sam.core.weather import create_simple_tmy_csv
from cli_anything.sam.core.results import (
    export_results_json, export_results_csv, export_results_text,
)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def synthetic_weather(tmp_path):
    """Create a synthetic weather CSV for testing."""
    path = str(tmp_path / "synthetic.csv")
    create_simple_tmy_csv(lat=39.74, lon=-104.99, output_path=path)
    print(f"\n  Synthetic weather: {path}")
    return path


def _require_pysam():
    """Skip test with clear message if PySAM not installed."""
    try:
        import PySAM
    except ImportError:
        pytest.skip(
            "PySAM not installed — install with: pip install NREL-PySAM\n"
            "PySAM is a REQUIRED dependency for cli-anything-sam."
        )


def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed command.
    """
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name) if (shutil := __import__("shutil")) else None
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(
            f"{name} not found in PATH. Install with:\n"
            f"  cd SAM/agent-harness && pip install -e ."
        )
    module = "cli_anything.sam.sam_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1: Basic PVWatts Simulation
# ─────────────────────────────────────────────────────────────────────────────

class TestPVWattsBasic:
    """Basic PVWatts residential simulation with synthetic weather."""

    def test_pvwatts_with_synthetic_weather(self, tmp_dir, synthetic_weather):
        """Simulate PVWatts with synthetic weather → verify annual energy > 0."""
        _require_pysam()

        proj = create_project(
            name="Denver PV Basic",
            technology="pvwatts",
            financial="none",
            capacity_kw=6.0,
            location={"lat": 39.74, "lon": -104.99, "elev": 1611, "tz": -7},
        )
        proj["inputs"]["weather_file"] = synthetic_weather

        results = simulate_project(proj)

        assert results is not None, "Simulation returned no results"
        assert "annual_energy" in results, "Missing annual_energy in results"
        assert results["annual_energy"] > 0, \
            f"annual_energy should be > 0, got {results['annual_energy']}"
        assert "capacity_factor" in results
        assert results["capacity_factor"] > 0

        print(f"\n  Annual energy: {results['annual_energy']:,.1f} kWh")
        print(f"  Capacity factor: {results['capacity_factor']:.1f}%")

    def test_pvwatts_results_stored_in_project(self, tmp_dir, synthetic_weather):
        """Verify results are stored in project dict after simulation."""
        _require_pysam()

        proj = create_project("Test PV", technology="pvwatts", financial="none")
        proj["inputs"]["weather_file"] = synthetic_weather
        simulate_project(proj)

        assert proj["results"] is not None
        assert "annual_energy" in proj["results"]


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2: PVWatts + Financial Analysis
# ─────────────────────────────────────────────────────────────────────────────

class TestPVWattsFinancial:
    """PVWatts with residential financial model."""

    def test_pvwatts_lcoe_financial(self, tmp_dir, synthetic_weather):
        """Simulate PVWatts + LCOE financial model → verify LCOE output.

        Uses the LCOE Fixed Charge Rate model (simpler than Cashloan residential
        which requires a separate utility rate module for net metering).
        """
        _require_pysam()

        proj = create_project(
            name="Denver PV LCOE",
            technology="pvwatts",
            financial="lcoe",
            capacity_kw=6.0,
        )
        proj["inputs"]["weather_file"] = synthetic_weather
        proj["financial_inputs"]["capital_cost"] = 18000.0
        proj["financial_inputs"]["fixed_operating_cost"] = 200.0

        results = simulate_project(proj)

        assert "annual_energy" in results
        assert results["annual_energy"] > 0

        print(f"\n  Annual energy: {results['annual_energy']:,.1f} kWh")
        if "lcoe_nominal" in results:
            assert results["lcoe_nominal"] > 0
            print(f"  LCOE: ${results['lcoe_nominal']:.4f}/kWh")
        if "lcoe_real" in results:
            print(f"  LCOE real: ${results['lcoe_real']:.4f}/kWh")


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3: Save/Load Roundtrip with Results
# ─────────────────────────────────────────────────────────────────────────────

class TestSaveLoadRoundtrip:
    """Project persistence with simulation results."""

    def test_save_and_reload_project(self, tmp_dir):
        """Save project → reload → verify all fields preserved."""
        proj = create_project(
            name="Roundtrip Test",
            technology="pvwatts",
            financial="residential",
            capacity_kw=5.0,
            location={"lat": 35.0, "lon": -90.0},
        )
        path = os.path.join(tmp_dir, "roundtrip.sam.json")
        save_project(proj, path)

        loaded = open_project(path)
        assert loaded["name"] == "Roundtrip Test"
        assert loaded["technology"] == "pvwatts"
        assert loaded["financial"] == "residential"
        assert loaded["inputs"]["system_capacity"] == 5.0
        assert loaded["inputs"]["location"]["lat"] == 35.0

        print(f"\n  Roundtrip project: {path}")
        print(f"  File size: {Path(path).stat().st_size:,} bytes")

    def test_results_preserved_after_save_load(self, tmp_dir, synthetic_weather):
        """Simulate → save → reload → results still present."""
        _require_pysam()

        proj = create_project("Results Persist", technology="pvwatts", financial="none")
        proj["inputs"]["weather_file"] = synthetic_weather
        simulate_project(proj)

        path = os.path.join(tmp_dir, "with_results.sam.json")
        save_project(proj, path)
        loaded = open_project(path)

        assert loaded["results"] is not None
        assert "annual_energy" in loaded["results"]
        assert loaded["results"]["annual_energy"] > 0


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4: Results Export Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class TestResultsExport:
    """Full export workflow after simulation."""

    def test_export_json(self, tmp_dir, synthetic_weather):
        """Simulate → export JSON → verify format."""
        _require_pysam()

        proj = create_project("Export JSON Test", technology="pvwatts", financial="none")
        proj["inputs"]["weather_file"] = synthetic_weather
        results = simulate_project(proj)

        out = os.path.join(tmp_dir, "results.json")
        path = export_results_json(results, out)

        assert Path(path).exists(), f"JSON not created: {path}"
        size = Path(path).stat().st_size
        assert size > 10, f"JSON suspiciously small: {size} bytes"
        loaded = json.loads(Path(path).read_text())
        assert "annual_energy" in loaded
        assert loaded["annual_energy"] > 0

        print(f"\n  JSON: {path} ({size:,} bytes)")
        print(f"  annual_energy: {loaded['annual_energy']:,.1f} kWh")

    def test_export_csv(self, tmp_dir, synthetic_weather):
        """Simulate → export CSV → verify structure."""
        _require_pysam()

        proj = create_project("Export CSV Test", technology="pvwatts", financial="none")
        proj["inputs"]["weather_file"] = synthetic_weather
        results = simulate_project(proj)

        out = os.path.join(tmp_dir, "results.csv")
        path = export_results_csv(results, out)

        assert Path(path).exists(), f"CSV not created: {path}"
        content = Path(path).read_text()
        assert "annual_energy" in content
        assert "Metric" in content  # Header row

        import csv
        with open(path) as f:
            rows = list(csv.reader(f))
        assert len(rows) > 2, "CSV should have more than 2 rows"

        print(f"\n  CSV: {path} ({Path(path).stat().st_size:,} bytes)")
        print(f"  Rows: {len(rows)}")

    def test_export_text_report(self, tmp_dir, synthetic_weather):
        """Simulate → export text report → verify content."""
        _require_pysam()

        proj = create_project("Export TXT Test", technology="pvwatts", financial="none")
        proj["inputs"]["weather_file"] = synthetic_weather
        results = simulate_project(proj)

        out = os.path.join(tmp_dir, "report.txt")
        path = export_results_text(results, out)

        assert Path(path).exists(), f"TXT not created: {path}"
        content = Path(path).read_text()
        assert "SAM Simulation Results" in content
        assert "ENERGY RESULTS" in content

        print(f"\n  Report: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 5: Synthetic Weather Coverage
# ─────────────────────────────────────────────────────────────────────────────

class TestSyntheticWeather:
    """Test the synthetic weather file generation and simulation."""

    def test_synthetic_weather_enables_simulation(self, tmp_dir):
        """Synthetic weather file allows PVWatts to run (testing only)."""
        _require_pysam()

        wf = os.path.join(tmp_dir, "synthetic.csv")
        create_simple_tmy_csv(lat=34.05, lon=-118.24, output_path=wf)  # Los Angeles

        assert Path(wf).exists()
        assert Path(wf).stat().st_size > 1000

        proj = create_project("LA Solar Test", technology="pvwatts", financial="none")
        proj["inputs"]["weather_file"] = wf
        proj["inputs"]["system_capacity"] = 5.0

        results = simulate_project(proj)
        assert results["annual_energy"] > 0
        print(f"\n  LA synthetic annual: {results['annual_energy']:,.1f} kWh")

    def test_larger_system_produces_more_energy(self, tmp_dir):
        """Larger system capacity → more annual energy (proportional scaling)."""
        _require_pysam()

        proj_small = create_project("Small PV", technology="pvwatts", financial="none",
                                    capacity_kw=3.0)
        proj_large = create_project("Large PV", technology="pvwatts", financial="none",
                                    capacity_kw=10.0)

        res_small = simulate_project(proj_small)
        res_large = simulate_project(proj_large)

        assert res_large["annual_energy"] > res_small["annual_energy"], \
            f"Larger system should produce more energy: {res_large['annual_energy']} vs {res_small['annual_energy']}"
        ratio = res_large["annual_energy"] / res_small["annual_energy"]
        assert 2.0 < ratio < 5.0, f"Energy ratio should be ~3.3x (10/3), got {ratio:.2f}"
        print(f"\n  Small (3 kW): {res_small['annual_energy']:,.1f} kWh")
        print(f"  Large (10 kW): {res_large['annual_energy']:,.1f} kWh")
        print(f"  Ratio: {ratio:.2f}x")


# ─────────────────────────────────────────────────────────────────────────────
# CLI Subprocess Tests
# ─────────────────────────────────────────────────────────────────────────────

import shutil as _shutil


def _resolve_cli_cmd(name):
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = _shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(
            f"{name} not found in PATH. Install with:\n"
            f"  cd SAM/agent-harness && pip install -e ."
        )
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m cli_anything.sam.sam_cli")
    return [sys.executable, "-m", "cli_anything.sam.sam_cli"]


class TestCLISubprocess:
    """Test the installed cli-anything-sam command via subprocess."""

    CLI_BASE = _resolve_cli_cmd("cli-anything-sam")

    def _run(self, args, check=True):
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "cli-anything-sam" in result.stdout
        print(f"\n  --help: OK")

    def test_version(self):
        result = self._run(["--version"])
        assert result.returncode == 0
        assert "1.0.0" in result.stdout
        print(f"\n  --version: {result.stdout.strip()}")

    def test_info_json(self):
        result = self._run(["--json", "info"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "pysam_installed" in data
        assert "technologies" in data
        print(f"\n  info --json: pysam={data['pysam_installed']}")

    def test_project_new_json(self, tmp_dir):
        out = os.path.join(tmp_dir, "test.sam.json")
        result = self._run([
            "--json", "project", "new",
            "-n", "CLITest",
            "-t", "pvwatts",
            "-f", "residential",
            "-o", out,
        ])
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["status"] == "ok"
        assert Path(out).exists()
        proj = json.loads(Path(out).read_text())
        assert proj["name"] == "CLITest"
        print(f"\n  project new: {out}")

    def test_full_simulation_workflow(self, tmp_dir):
        """Full workflow: create → set weather → simulate → results show."""
        _require_pysam()

        proj_path = os.path.join(tmp_dir, "workflow.sam.json")
        wf_path   = os.path.join(tmp_dir, "weather.csv")

        # Create synthetic weather
        create_simple_tmy_csv(39.74, -104.99, wf_path)

        # Create project
        result = self._run([
            "--json", "project", "new",
            "-n", "WorkflowTest",
            "-t", "pvwatts",
            "-f", "none",
            "-o", proj_path,
        ])
        assert result.returncode == 0, f"create failed: {result.stderr}"

        # Set weather
        result = self._run([
            "--json", "weather", "set", wf_path,
            "-p", proj_path, "-o", proj_path,
        ])
        assert result.returncode == 0, f"weather set failed: {result.stderr}"

        # Run simulation
        result = self._run(["--json", "simulate", "run", proj_path, "-o", proj_path])
        assert result.returncode == 0, f"simulate failed: {result.stderr}"
        sim_data = json.loads(result.stdout)
        assert sim_data["status"] == "ok"
        assert "annual_energy" in sim_data["results"]
        assert sim_data["results"]["annual_energy"] > 0

        # Show results
        result = self._run(["--json", "results", "show", proj_path])
        assert result.returncode == 0, f"results show failed: {result.stderr}"
        res_data = json.loads(result.stdout)
        assert "annual_energy" in res_data
        assert res_data["annual_energy"] > 0

        energy = res_data["annual_energy"]
        print(f"\n  Full workflow complete!")
        print(f"  Annual energy: {energy:,.1f} kWh")
        print(f"  Project: {proj_path} ({Path(proj_path).stat().st_size:,} bytes)")

    def test_simulate_check_json(self, tmp_dir):
        """simulate check returns readiness info."""
        proj_path = os.path.join(tmp_dir, "check.sam.json")
        self._run([
            "project", "new", "-n", "CheckTest", "-t", "pvwatts",
            "-f", "none", "-o", proj_path
        ])
        result = self._run(["--json", "simulate", "check", proj_path])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "ready" in data
        assert "issues" in data
        print(f"\n  simulate check: ready={data['ready']}, issues={data['issues']}")
