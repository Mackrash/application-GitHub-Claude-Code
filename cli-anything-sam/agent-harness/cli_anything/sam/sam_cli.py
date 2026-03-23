"""cli-anything-sam — Command-line interface for NREL's System Advisor Model (SAM).

Wraps PySAM (NREL-PySAM) to provide a full CLI + REPL for renewable energy simulation.

Usage:
    cli-anything-sam                          # Enter REPL
    cli-anything-sam project new -n MyPV -o project.sam.json
    cli-anything-sam simulate run project.sam.json
    cli-anything-sam results show project.sam.json
"""

import json
import os
import shlex
import sys
from pathlib import Path

import click

from cli_anything.sam.core.project import (
    create_project, open_project, save_project,
    get_project_info, set_input, set_financial_input,
    list_inputs, SUPPORTED_TECHNOLOGIES, SUPPORTED_FINANCIALS,
)
from cli_anything.sam.core.simulate import (
    simulate_project, get_simulation_summary, check_simulation_ready,
)
from cli_anything.sam.core.weather import (
    set_weather_file, get_weather_info, list_weather_files,
    create_simple_tmy_csv,
)
from cli_anything.sam.core.results import (
    export_results_json, export_results_csv,
    export_results_text, compare_results,
)
from cli_anything.sam.core.session import Session
from cli_anything.sam.utils.repl_skin import ReplSkin
from cli_anything.sam.utils.sam_backend import find_pysam, get_pysam_version

__version__ = "1.0.0"

_skin = ReplSkin("sam", version=__version__)

# Global session for REPL state
_session = Session(
    session_file=str(Path.home() / ".cli-anything-sam" / "session.json")
)


def _json_out(data, json_mode: bool):
    """Print data as JSON if json_mode, else return data for human formatting."""
    if json_mode:
        click.echo(json.dumps(data, indent=2, default=str))
    return data


def _load_project_arg(project_path: str) -> dict:
    """Load project from path or active session."""
    if project_path:
        return open_project(project_path)
    if _session.is_open():
        return _session.project
    raise click.UsageError(
        "No project open. Provide --project <path> or open a project first."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Main CLI group
# ═══════════════════════════════════════════════════════════════════════════════

@click.group(invoke_without_command=True)
@click.option("--json", "json_mode", is_flag=True, help="Output JSON for agent consumption")
@click.option("--project", "project_path", default=None, help="Project file to operate on")
@click.version_option(__version__, prog_name="cli-anything-sam")
@click.pass_context
def cli(ctx, json_mode, project_path):
    """cli-anything-sam — CLI harness for NREL System Advisor Model (SAM).

    Simulate solar PV, wind, battery, and geothermal projects using PySAM.

    \b
    Quick start:
      sam project new -n MyPV -t pvwatts -f residential -o my_project.sam.json
      sam simulate run my_project.sam.json
      sam results show my_project.sam.json
    """
    ctx.ensure_object(dict)
    ctx.obj["json_mode"] = json_mode
    ctx.obj["project_path"] = project_path

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ═══════════════════════════════════════════════════════════════════════════════
# project group
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group()
def project():
    """Create, open, save, and inspect SAM projects."""
    pass


@project.command("new")
@click.option("-n", "--name", required=True, help="Project name")
@click.option("-t", "--technology", default="pvwatts", show_default=True,
              type=click.Choice(list(SUPPORTED_TECHNOLOGIES)), help="Technology type")
@click.option("-f", "--financial", default="residential", show_default=True,
              type=click.Choice(list(SUPPORTED_FINANCIALS)), help="Financial model")
@click.option("-o", "--output", "output_path", required=True, help="Output .sam.json file")
@click.option("--lat", type=float, default=None, help="Site latitude")
@click.option("--lon", type=float, default=None, help="Site longitude")
@click.option("--capacity", type=float, default=None, help="System capacity (kW)")
@click.pass_context
def project_new(ctx, name, technology, financial, output_path, lat, lon, capacity):
    """Create a new SAM simulation project."""
    json_mode = ctx.obj["json_mode"]
    location = None
    if lat is not None or lon is not None:
        location = {}
        if lat is not None:
            location["lat"] = lat
        if lon is not None:
            location["lon"] = lon

    proj = create_project(
        name=name,
        technology=technology,
        financial=financial,
        output_path=output_path,
        location=location,
        capacity_kw=capacity,
    )
    _session.open_project(proj, output_path)

    info = get_project_info(proj)
    if json_mode:
        _json_out({"status": "ok", "project": proj, "info": info}, json_mode=True)
    else:
        _skin.success(f"Created project '{name}' → {output_path}")
        _skin.status_block(info, title="Project Info")


@project.command("open")
@click.argument("path")
@click.pass_context
def project_open(ctx, path):
    """Open an existing SAM project."""
    json_mode = ctx.obj["json_mode"]
    proj = open_project(path)
    _session.open_project(proj, path)
    info = get_project_info(proj)
    if json_mode:
        _json_out({"status": "ok", "project": proj, "info": info}, json_mode=True)
    else:
        _skin.success(f"Opened: {path}")
        _skin.status_block(info, title="Project Info")


@project.command("save")
@click.option("-o", "--output", "output_path", default=None, help="Output path (default: original path)")
@click.pass_context
def project_save(ctx, output_path):
    """Save the currently open project."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(ctx.obj.get("project_path"))
    path = output_path or _session.project_path
    if not path:
        raise click.UsageError("No output path. Use -o to specify.")
    saved = save_project(proj, path)
    _session.modified = False
    if json_mode:
        _json_out({"status": "ok", "path": saved}, json_mode=True)
    else:
        _skin.success(f"Saved to {saved}")


@project.command("info")
@click.argument("path", required=False)
@click.pass_context
def project_info(ctx, path):
    """Show project summary information."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(path or ctx.obj.get("project_path"))
    info = get_project_info(proj)
    if json_mode:
        _json_out(info, json_mode=True)
    else:
        _skin.status_block(info, title="Project Info")


@project.command("set")
@click.argument("key")
@click.argument("value")
@click.option("-o", "--output", "output_path", default=None)
@click.pass_context
def project_set(ctx, key, value, output_path):
    """Set a project input parameter.

    KEY can use dot notation for nested fields (e.g. location.lat).

    \b
    Examples:
      sam project set system_capacity 10.0
      sam project set location.lat 40.5
      sam project set tilt 25
    """
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(ctx.obj.get("project_path"))

    # Attempt type coercion
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value

    # Determine if financial or tech input
    fin_keys = {"analysis_period", "inflation_rate", "real_discount_rate",
                "total_installed_cost", "federal_tax_rate", "state_tax_rate",
                "property_tax_rate", "loan_term", "loan_rate"}
    if key in fin_keys:
        set_financial_input(proj, key, parsed)
    else:
        set_input(proj, key, parsed)

    _session.update_project(proj, f"set {key}={value}")

    # Auto-save if path available
    save_path = output_path or _session.project_path
    if save_path:
        save_project(proj, save_path)

    if json_mode:
        _json_out({"status": "ok", "key": key, "value": parsed}, json_mode=True)
    else:
        _skin.success(f"Set {key} = {parsed}")


@project.command("inputs")
@click.argument("path", required=False)
@click.pass_context
def project_inputs(ctx, path):
    """List all project input parameters."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(path or ctx.obj.get("project_path"))
    inputs = list_inputs(proj)
    if json_mode:
        _json_out(inputs, json_mode=True)
    else:
        _skin.section("Technology Inputs")
        for k, v in inputs.items():
            _skin.status(k, str(v))
        _skin.section("Financial Inputs")
        for k, v in proj.get("financial_inputs", {}).items():
            _skin.status(k, str(v))


# ═══════════════════════════════════════════════════════════════════════════════
# simulate group
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group()
def simulate():
    """Run SAM/PySAM simulations."""
    pass


@simulate.command("run")
@click.argument("path", required=False)
@click.option("-o", "--output", "output_path", default=None,
              help="Save updated project (with results) to this path")
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
def simulate_run(ctx, path, output_path, verbose):
    """Run a simulation for a SAM project.

    \b
    Example:
      sam simulate run my_project.sam.json
      sam simulate run my_project.sam.json -o results.sam.json
    """
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(path or ctx.obj.get("project_path"))

    # Check readiness
    ready, issues = check_simulation_ready(proj)
    if issues:
        for issue in issues:
            _skin.warning(issue)

    if not json_mode:
        _skin.info(f"Running {proj.get('technology')} simulation...")

    results = simulate_project(proj, verbose=verbose)
    _session.last_results = results

    # Save if path given
    save_path = output_path or path or _session.project_path
    if save_path:
        save_project(proj, save_path)

    if json_mode:
        _json_out({"status": "ok", "results": results}, json_mode=True)
    else:
        _skin.success("Simulation complete!")
        summary = get_simulation_summary(results)
        _skin.status_block(summary, title="Results Summary")


@simulate.command("check")
@click.argument("path", required=False)
@click.pass_context
def simulate_check(ctx, path):
    """Check if a project is ready to simulate."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(path or ctx.obj.get("project_path"))
    ready, issues = check_simulation_ready(proj)
    if json_mode:
        _json_out({"ready": ready, "issues": issues}, json_mode=True)
    else:
        if ready:
            _skin.success("Project is ready to simulate")
        else:
            _skin.warning(f"{len(issues)} issue(s) found:")
            for issue in issues:
                _skin.info(f"  • {issue}")


# ═══════════════════════════════════════════════════════════════════════════════
# weather group
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group()
def weather():
    """Manage weather resource files."""
    pass


@weather.command("set")
@click.argument("weather_file")
@click.option("-p", "--project", "project_path_opt", default=None)
@click.option("-o", "--output", "output_path", default=None)
@click.pass_context
def weather_set(ctx, weather_file, project_path_opt, output_path):
    """Set the weather file for a project."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(project_path_opt or ctx.obj.get("project_path"))
    set_weather_file(proj, weather_file)
    _session.update_project(proj, f"set weather_file={weather_file}")

    save_path = output_path or _session.project_path
    if save_path:
        save_project(proj, save_path)

    if json_mode:
        _json_out({"status": "ok", "weather_file": weather_file}, json_mode=True)
    else:
        _skin.success(f"Weather file set: {weather_file}")


@weather.command("info")
@click.argument("weather_file")
@click.pass_context
def weather_info(ctx, weather_file):
    """Show metadata for a weather file."""
    json_mode = ctx.obj["json_mode"]
    info = get_weather_info(weather_file)
    if json_mode:
        _json_out(info, json_mode=True)
    else:
        _skin.status_block(info, title=f"Weather File: {Path(weather_file).name}")


@weather.command("list")
@click.argument("directory", default=".")
@click.pass_context
def weather_list(ctx, directory):
    """List weather files in a directory."""
    json_mode = ctx.obj["json_mode"]
    files = list_weather_files(directory)
    if json_mode:
        _json_out(files, json_mode=True)
    else:
        if not files:
            _skin.warning(f"No weather files found in {directory}")
        else:
            _skin.table(
                ["File", "Format", "Size (KB)"],
                [[Path(f["file"]).name, f["format"], str(f["size_kb"])] for f in files]
            )


@weather.command("create-synthetic")
@click.option("--lat", type=float, required=True, help="Latitude")
@click.option("--lon", type=float, required=True, help="Longitude")
@click.option("-o", "--output", "output_path", required=True, help="Output CSV file")
@click.option("--ghi", type=float, default=5.0, help="Avg daily GHI (kWh/m²/day)")
@click.option("--temp", type=float, default=15.0, help="Avg temperature (°C)")
@click.pass_context
def weather_create_synthetic(ctx, lat, lon, output_path, ghi, temp):
    """Create a synthetic weather file for testing.

    WARNING: Not for real analysis — use measured data for actual projects.
    """
    json_mode = ctx.obj["json_mode"]
    path = create_simple_tmy_csv(lat, lon, output_path, avg_ghi=ghi, avg_temp=temp)
    if json_mode:
        _json_out({"status": "ok", "path": path, "warning": "Synthetic data — not for real analysis"}, json_mode=True)
    else:
        _skin.success(f"Synthetic weather file created: {path}")
        _skin.warning("This file is for testing only — use real measured data for actual projects")


# ═══════════════════════════════════════════════════════════════════════════════
# results group
# ═══════════════════════════════════════════════════════════════════════════════

@cli.group()
def results():
    """View and export simulation results."""
    pass


@results.command("show")
@click.argument("path", required=False)
@click.pass_context
def results_show(ctx, path):
    """Show simulation results for a project."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(path or ctx.obj.get("project_path"))
    res = proj.get("results")
    if not res:
        if json_mode:
            _json_out({"error": "No results yet — run `simulate run` first"}, json_mode=True)
        else:
            _skin.warning("No results yet — run: sam simulate run <project>")
        return

    if json_mode:
        _json_out(res, json_mode=True)
    else:
        report = export_results_text(res)
        click.echo(report)


@results.command("export")
@click.argument("path", required=False)
@click.option("-o", "--output", "output_path", required=True, help="Output file")
@click.option("-f", "--format", "fmt", default="json",
              type=click.Choice(["json", "csv", "txt"]), help="Export format")
@click.pass_context
def results_export(ctx, path, output_path, fmt):
    """Export simulation results to a file."""
    json_mode = ctx.obj["json_mode"]
    proj = _load_project_arg(path or ctx.obj.get("project_path"))
    res = proj.get("results")
    if not res:
        raise click.UsageError("No results — run simulate first.")

    if fmt == "json":
        saved = export_results_json(res, output_path)
    elif fmt == "csv":
        saved = export_results_csv(res, output_path)
    else:
        saved = export_results_text(res, output_path)

    if json_mode:
        _json_out({"status": "ok", "path": saved, "format": fmt}, json_mode=True)
    else:
        _skin.success(f"Results exported ({fmt}): {saved}")


# ═══════════════════════════════════════════════════════════════════════════════
# info command
# ═══════════════════════════════════════════════════════════════════════════════

@cli.command("info")
@click.pass_context
def info_cmd(ctx):
    """Show CLI version and PySAM installation info."""
    json_mode = ctx.obj["json_mode"]
    try:
        ver = get_pysam_version()
        pysam_ok = True
    except RuntimeError as e:
        ver = str(e)
        pysam_ok = False

    data = {
        "cli_version":   __version__,
        "pysam_installed": pysam_ok,
        "pysam_version": ver,
        "technologies":  list(SUPPORTED_TECHNOLOGIES.keys()),
        "financial_models": list(SUPPORTED_FINANCIALS.keys()),
    }

    if json_mode:
        _json_out(data, json_mode=True)
    else:
        _skin.status_block({
            "CLI Version":   __version__,
            "PySAM":         f"{'✓ ' + ver if pysam_ok else '✗ NOT INSTALLED'}",
            "Technologies":  ", ".join(SUPPORTED_TECHNOLOGIES.keys()),
            "Financial":     ", ".join(SUPPORTED_FINANCIALS.keys()),
        }, title="cli-anything-sam")


# ═══════════════════════════════════════════════════════════════════════════════
# REPL
# ═══════════════════════════════════════════════════════════════════════════════

REPL_COMMANDS = {
    "project new":    "Create a new project",
    "project open":   "Open an existing project",
    "project save":   "Save the current project",
    "project info":   "Show project info",
    "project set":    "Set an input parameter",
    "project inputs": "List all inputs",
    "simulate run":   "Run simulation",
    "simulate check": "Check simulation readiness",
    "weather set":    "Set weather file",
    "weather info":   "Weather file metadata",
    "weather list":   "List weather files",
    "results show":   "Show simulation results",
    "results export": "Export results",
    "info":           "CLI and PySAM version info",
    "status":         "Session status",
    "undo":           "Undo last change",
    "redo":           "Redo last change",
    "help":           "Show this help",
    "quit":           "Exit the REPL",
}


@cli.command("repl")
@click.pass_context
def repl(ctx):
    """Start the interactive REPL session."""
    _skin.print_banner()

    # Check PySAM
    try:
        ver = get_pysam_version()
        _skin.success(f"PySAM {ver} ready")
    except RuntimeError:
        _skin.error("PySAM not installed! Run: pip install NREL-PySAM")
        _skin.hint("Simulations will fail until PySAM is installed.")

    # Restore session
    state = _session.load_session()
    if state.get("project_path") and Path(state["project_path"]).exists():
        try:
            proj = open_project(state["project_path"])
            _session.open_project(proj, state["project_path"])
            _skin.info(f"Restored: {state['project_path']}")
        except Exception:
            pass

    pt_session = _skin.create_prompt_session()

    while True:
        try:
            ctx_name = _session.context_name()
            line = _skin.get_input(pt_session, context=ctx_name, modified=_session.modified)
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue

        cmd = line.strip().lower()

        if cmd in ("quit", "exit", "q"):
            break

        if cmd == "help":
            _skin.help(REPL_COMMANDS)
            continue

        if cmd == "status":
            status = _session.status()
            _skin.status_block({k: str(v) for k, v in status.items()}, title="Session Status")
            continue

        if cmd == "undo":
            ok, msg = _session.undo()
            (_skin.success if ok else _skin.warning)(msg)
            continue

        if cmd == "redo":
            ok, msg = _session.redo()
            (_skin.success if ok else _skin.warning)(msg)
            continue

        # Dispatch to Click subcommands
        try:
            args = shlex.split(line)
            cli.main(args=args, standalone_mode=False, obj={"json_mode": False, "project_path": None})
        except SystemExit:
            pass
        except click.UsageError as e:
            _skin.error(str(e))
        except click.ClickException as e:
            _skin.error(e.format_message())
        except Exception as e:
            _skin.error(f"Error: {e}")

    _session.save_session()
    _skin.print_goodbye()


def main():
    # Fix Windows console encoding for Unicode characters (checkmarks, arrows, etc.)
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    cli(obj={})


if __name__ == "__main__":
    main()
