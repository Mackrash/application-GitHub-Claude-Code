#!/usr/bin/env python3
"""Génère les facteurs solaires mensuels SF[] via PySAM pour le calculateur PV NC.

Usage:
    python generate_sf.py
    python generate_sf.py --lat -22.27 --lon 166.44 --api-key YOUR_NREL_KEY

Clé API NREL gratuite : https://developer.nrel.gov/signup/
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description='Génère SF[] via PySAM Pvwattsv8')
    parser.add_argument('--lat',     type=float, default=-22.27)
    parser.add_argument('--lon',     type=float, default=166.44)
    parser.add_argument('--tilt',    type=float, default=15.0)
    parser.add_argument('--azimuth', type=float, default=0.0)
    parser.add_argument('--losses',  type=float, default=14.0)
    parser.add_argument('--api-key', type=str,   default='')
    args = parser.parse_args()

    try:
        import PySAM.Pvwattsv8 as pv
        import PySAM.ResourceTools as rt
        import numpy as np
    except ImportError:
        print("ERREUR: pip install NREL-PySAM numpy")
        print("Facteurs actuels (estimation Nouméa):")
        print("const SF=[1.15,1.08,1.05,0.92,0.82,0.75,0.78,0.85,0.95,1.05,1.12,1.18];")
        return

    if not args.api_key:
        print("Utiliser --api-key YOUR_KEY (gratuit sur https://developer.nrel.gov/signup/)")
        print("Facteurs actuels:")
        print("const SF=[1.15,1.08,1.05,0.92,0.82,0.75,0.78,0.85,0.95,1.05,1.12,1.18];")
        return

    model = pv.default('PVWattsResidential')
    model.SystemDesign.system_capacity = 1.0
    model.SystemDesign.tilt = args.tilt
    model.SystemDesign.azimuth = args.azimuth
    model.SystemDesign.losses = args.losses

    weather = rt.FetchResourceFiles(tech='solar', lat=args.lat, lon=args.lon,
                                    api_key=args.api_key, email='user@example.com')
    model.SolarResource.solar_resource_file = weather.resource_file_paths[0]
    model.execute()

    ac  = np.array(model.Outputs.ac)
    dim = [31,28,31,30,31,30,31,31,30,31,30,31]
    mois = ['Jan','Fev','Mar','Avr','Mai','Jun','Jul','Aou','Sep','Oct','Nov','Dec']
    monthly, h = [], 0
    for d in dim:
        monthly.append(sum(ac[h:h+d*24])/1000); h += d*24

    avg = sum(monthly)/12
    sf  = [round(m/avg,2) for m in monthly]
    print(f"// PySAM Pvwattsv8 — lat={args.lat}, lon={args.lon}, tilt={args.tilt}°")
    print(f"// Production annuelle 1 kWc : {sum(monthly):.0f} kWh")
    print(f"const SF=[{','.join(str(s) for s in sf)}];")
    print(f"//         {' '.join(f'{m:>4}' for m in mois)}")

if __name__ == '__main__':
    main()
