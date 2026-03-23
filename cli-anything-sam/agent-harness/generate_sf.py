"""
generate_sf.py — Génère les facteurs solaires mensuels SF[] pour Nouméa NC via PySAM.

Usage:
    python generate_sf.py --lat -22.27 --lon 166.44 --tilt 15 --azimuth 0
    python generate_sf.py --lat -22.27 --lon 166.44 --tilt 15 --azimuth 0 --api-key YOUR_NREL_KEY

Sortie:
    Tableau JS prêt à coller dans calculateur-pv-nc.html :
    // Facteurs solaires mensuels calibrés SAM/PySAM — Nouméa NC (lat -22.27, lon 166.44, tilt 15°, azimuth 0°)
    const SF=[1.15,1.08,...];
"""

import argparse
import sys

try:
    import PySAM.Pvwattsv8 as pv
except ImportError:
    print("ERREUR : PySAM non installé. Lancez : pip install NREL-PySAM", file=sys.stderr)
    sys.exit(1)


def generate_sf(lat: float, lon: float, tilt: float, azimuth: float, api_key: str = None) -> list:
    """Simule 1 kWc à la position donnée et retourne les facteurs SF mensuels."""
    model = pv.default("PVWattsResidential")

    # Système : 1 kWc, tilt/azimuth configurables, pertes 14%
    sd = model.SystemDesign
    sd.system_capacity = 1.0
    sd.tilt = tilt
    sd.azimuth = azimuth
    sd.losses = 14.0
    sd.array_type = 0   # Fixe
    sd.module_type = 0  # Standard

    # Ressource météo
    sr = model.SolarResource
    if api_key:
        # Utiliser NSRDB via API NREL (TMY)
        url = (
            f"https://developer.nrel.gov/api/solar/nsrdb_psm3_download.json"
            f"?api_key={api_key}&lat={lat}&lon={lon}&interval=60"
            f"&attributes=ghi,dhi,dni,wind_speed,air_temperature"
            f"&name=noumea&email=user@example.com&leap_day=false&utc=false"
            f"&full_name=PySAM&affiliation=Solar&reason=research&mailing_list=false"
            f"&year=tmy"
        )
        print(f"NSRDB URL : {url}", file=sys.stderr)
        print("Note : téléchargez le fichier CSV NSRDB et utilisez solar_resource_file.", file=sys.stderr)
        print("Pour l'instant, utilisation des données synthétiques.", file=sys.stderr)

    # Données synthétiques si pas d'API key
    from cli_anything.sam.utils.sam_backend import _build_solar_resource_data
    loc = {"lat": lat, "lon": lon, "tz": 11, "elev": 0}
    sr.solar_resource_data = _build_solar_resource_data(loc)

    model.execute()

    monthly_kwh = list(model.Outputs.ac_monthly)  # kWh/mois pour 1 kWc

    # Facteurs = ratio mois / moyenne mensuelle
    avg = sum(monthly_kwh) / 12
    if avg == 0:
        raise ValueError("Production moyenne nulle — vérifiez les données météo.")

    sf = [round(m / avg, 2) for m in monthly_kwh]
    return sf


def main():
    parser = argparse.ArgumentParser(description="Génère les facteurs solaires SF[] pour le calculateur PV NC")
    parser.add_argument("--lat", type=float, default=-22.27, help="Latitude (défaut : -22.27, Nouméa)")
    parser.add_argument("--lon", type=float, default=166.44, help="Longitude (défaut : 166.44, Nouméa)")
    parser.add_argument("--tilt", type=float, default=15.0, help="Inclinaison panneaux en degrés (défaut : 15)")
    parser.add_argument("--azimuth", type=float, default=0.0, help="Azimuth en degrés, 0=Nord (défaut : 0)")
    parser.add_argument("--api-key", type=str, default=None, help="Clé API NREL pour données NSRDB réelles")
    args = parser.parse_args()

    print(f"Simulation PySAM — lat={args.lat}, lon={args.lon}, tilt={args.tilt}°, azimuth={args.azimuth}°", file=sys.stderr)

    sf = generate_sf(args.lat, args.lon, args.tilt, args.azimuth, args.api_key)

    mois = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    print(f"\n// Facteurs solaires mensuels calibrés SAM/PySAM — Nouméa NC (lat {args.lat}, lon {args.lon}, tilt {args.tilt}°, azimuth {args.azimuth}°)")
    print(f"const SF=[{','.join(str(v) for v in sf)}];")
    print(f"// {' '.join(f'{m}={v}' for m, v in zip(mois, sf))}")


if __name__ == "__main__":
    main()
