"""SAM weather resource management — fetch, inspect, and set weather files."""

import json
import os
from pathlib import Path

SUPPORTED_WEATHER_FORMATS = {
    ".epw":  "EnergyPlus Weather (solar)",
    ".srw":  "SAM Resource Weather (wind)",
    ".csv":  "SAM CSV Weather (solar/wind)",
    ".tm2":  "TMY2 (legacy solar)",
    ".tm3":  "TMY3 (legacy solar)",
    ".smw":  "SAM Meteorological Weather",
}


def set_weather_file(project: dict, weather_file: str) -> dict:
    """Set the weather file for a project.

    Args:
        project: Project dict (modified in-place).
        weather_file: Path to weather file.

    Returns:
        Updated project dict.

    Raises:
        FileNotFoundError: If weather file does not exist.
        ValueError: If file format is not supported.
    """
    path = Path(weather_file)
    if not path.exists():
        raise FileNotFoundError(f"Weather file not found: {weather_file}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_WEATHER_FORMATS:
        raise ValueError(
            f"Unsupported weather file format '{suffix}'.\n"
            f"Supported: {', '.join(SUPPORTED_WEATHER_FORMATS)}"
        )

    project["inputs"]["weather_file"] = str(path.resolve())
    return project


def get_weather_info(weather_file: str) -> dict:
    """Extract metadata from a weather file.

    Args:
        weather_file: Path to weather file.

    Returns:
        Dict with metadata (lat, lon, elevation, source, location name, etc.).
    """
    path = Path(weather_file)
    if not path.exists():
        raise FileNotFoundError(f"Weather file not found: {weather_file}")

    info = {
        "file":   str(path.resolve()),
        "format": SUPPORTED_WEATHER_FORMATS.get(path.suffix.lower(), "unknown"),
        "size_kb": round(path.stat().st_size / 1024, 1),
    }

    suffix = path.suffix.lower()

    if suffix == ".epw":
        info.update(_parse_epw_header(path))
    elif suffix == ".srw":
        info.update(_parse_srw_header(path))
    elif suffix == ".csv":
        info.update(_parse_sam_csv_header(path))

    return info


def _parse_epw_header(path: Path) -> dict:
    """Parse EPW file header for location metadata."""
    meta = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            first_line = f.readline().strip()
        # LOCATION,City,State,Country,Source,WMO,Lat,Lon,TZ,Elev
        if first_line.startswith("LOCATION"):
            parts = first_line.split(",")
            if len(parts) >= 10:
                meta["city"]      = parts[1].strip()
                meta["state"]     = parts[2].strip()
                meta["country"]   = parts[3].strip()
                meta["source"]    = parts[4].strip()
                meta["latitude"]  = float(parts[6])
                meta["longitude"] = float(parts[7])
                meta["timezone"]  = float(parts[8])
                meta["elevation"] = float(parts[9])
    except Exception:
        pass
    return meta


def _parse_srw_header(path: Path) -> dict:
    """Parse SRW (SAM Resource Weather) file header."""
    meta = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = [f.readline().strip() for _ in range(3)]
        # Line 1: City, State, Country, Lat, Lon, Year, Hour
        parts = lines[0].split(",")
        if len(parts) >= 5:
            meta["city"]      = parts[0].strip()
            meta["state"]     = parts[1].strip()
            meta["country"]   = parts[2].strip()
            meta["latitude"]  = float(parts[3]) if parts[3].strip() else None
            meta["longitude"] = float(parts[4]) if parts[4].strip() else None
    except Exception:
        pass
    return meta


def _parse_sam_csv_header(path: Path) -> dict:
    """Parse SAM CSV weather file header."""
    meta = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            first_line = f.readline().strip()
        # SAM CSV: Source, Location ID, City, State, Lat, Lon, TZ, Elev, Local Time Zone, ...
        parts = first_line.split(",")
        if len(parts) >= 8:
            meta["source"]    = parts[0].strip()
            meta["location_id"] = parts[1].strip()
            meta["city"]      = parts[2].strip()
            meta["state"]     = parts[3].strip()
            meta["latitude"]  = float(parts[4]) if parts[4].strip() else None
            meta["longitude"] = float(parts[5]) if parts[5].strip() else None
            meta["timezone"]  = float(parts[6]) if parts[6].strip() else None
            meta["elevation"] = float(parts[7]) if parts[7].strip() else None
    except Exception:
        pass
    return meta


def fetch_nsrdb_weather(
    lat: float,
    lon: float,
    year: int,
    api_key: str,
    output_dir: str = ".",
    email: str = "user@example.com",
) -> str:
    """Download a weather file from NREL's NSRDB (requires API key).

    Args:
        lat: Latitude.
        lon: Longitude.
        year: Year (e.g. 2020). Use "tmy" for typical meteorological year.
        api_key: NREL developer API key (get one at developer.nrel.gov/signup).
        output_dir: Directory to save the weather file.
        email: Email address (required by NSRDB API).

    Returns:
        Path to downloaded weather file.

    Raises:
        RuntimeError: If download fails or API key is invalid.
    """
    try:
        import PySAM.ResourceTools as rt
    except ImportError:
        raise RuntimeError(
            "NREL-PySAM is required for weather download.\n"
            "Install: pip install NREL-PySAM"
        )

    if not api_key or api_key == "DEMO_KEY":
        raise RuntimeError(
            "A valid NREL API key is required for NSRDB downloads.\n"
            "Get a free key at: https://developer.nrel.gov/signup/\n"
            "Then use: sam weather set-api-key <key>"
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build NSRDB download URL
    filename = f"nsrdb_{lat}_{lon}_{year}.csv"
    out_file = str(output_path / filename)

    try:
        downloader = rt.SRRPResourceDownloader()
        downloader.latitude  = lat
        downloader.longitude = lon
        downloader.api_key   = api_key
        downloader.email     = email
        downloader.year      = str(year)
        downloader.attributes = "ghi,dhi,dni,wind_speed,air_temperature,solar_zenith_angle"
        downloader.download(out_file)
        return out_file
    except Exception as e:
        raise RuntimeError(f"NSRDB download failed: {e}") from e


def list_weather_files(directory: str = ".") -> list:
    """List all weather files in a directory.

    Returns:
        List of dicts with file, format, size_kb.
    """
    results = []
    base = Path(directory)
    if not base.is_dir():
        return results

    for ext in SUPPORTED_WEATHER_FORMATS:
        for f in sorted(base.glob(f"**/*{ext}")):
            results.append({
                "file":    str(f),
                "format":  SUPPORTED_WEATHER_FORMATS[ext],
                "size_kb": round(f.stat().st_size / 1024, 1),
            })

    return results


def create_simple_tmy_csv(
    lat: float,
    lon: float,
    output_path: str,
    avg_ghi: float = 5.0,
    avg_temp: float = 15.0,
) -> str:
    """Create a minimal synthetic TMY CSV for testing (not for real analysis).

    This creates a synthetic weather file that allows PySAM to run.
    For real analysis, always use measured or modeled weather data.

    Args:
        lat: Latitude.
        lon: Longitude.
        output_path: Output file path.
        avg_ghi: Average global horizontal irradiance (kWh/m²/day).
        avg_temp: Average temperature (°C).

    Returns:
        Path to created file.
    """
    import csv

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert daily avg to hourly peak (simplified)
    peak_ghi = avg_ghi * 1000 / 6  # assume 6 peak sun hours → W/m²

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        # SAM CSV header
        writer.writerow([
            "Synthetic", "000000", "Synthetic Location", "", lat, lon, 0, 0, 0,
            "Generated by cli-anything-sam", "", "", "", ""
        ])
        writer.writerow(["Source", "Location ID", "City", "State", "Latitude", "Longitude",
                         "Time Zone", "Elevation", "Local Time Zone", "Clearsky DHI",
                         "Clearsky DNI", "Clearsky GHI", "Dew Point", "DHI", "DNI",
                         "GHI", "Surface Albedo", "Pressure", "Relative Humidity",
                         "Solar Zenith Angle", "Temperature", "Wind Direction", "Wind Speed"])
        writer.writerow(["", "", "", "", "Degrees", "Degrees", "Hours", "Meters", "Hours",
                         "W/m2", "W/m2", "W/m2", "C", "W/m2", "W/m2", "W/m2", "",
                         "mbar", "%", "Degrees", "C", "Degrees", "m/s"])

        # 8760 hours of data
        import math
        for hour in range(8760):
            day_of_year = hour // 24
            hour_of_day = hour % 24
            # Simple diurnal pattern
            sun_angle = math.sin(math.pi * (hour_of_day - 6) / 12)
            ghi = max(0, peak_ghi * sun_angle) if 6 <= hour_of_day <= 18 else 0
            dhi = ghi * 0.2
            dni = ghi * 0.8 if ghi > 0 else 0
            temp = avg_temp + 5 * math.sin(2 * math.pi * day_of_year / 365)
            writer.writerow([
                "", "", "", "", lat, lon, 0, 0, 0,
                round(ghi * 1.1), round(dni * 1.1), round(ghi * 1.1),
                round(temp - 5), round(dhi), round(dni), round(ghi),
                0.2, 1013, 50, 0 if ghi == 0 else 30,
                round(temp), 180, 3.0
            ])

    return str(path.resolve())
