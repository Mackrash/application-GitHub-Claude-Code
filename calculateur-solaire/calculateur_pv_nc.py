"""Calculateur PV Nouvelle-Calédonie — Solar Concept v2.0.

Application Streamlit de dimensionnement photovoltaïque pour la NC.
Charte graphique : Orange #F07020, Anthracite #1A1A2E, Blanc #FFFFFF.
Theme : Solar 2030 — Dark mode, glassmorphism, graphiques modernes.
"""

import base64
import math
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ===================== CONSTANTES =====================

SOLAR_FACTORS: list[float] = [
    1.18, 1.12, 1.08, 0.95, 0.85, 0.78,
    0.80, 0.88, 0.98, 1.08, 1.15, 1.18,
]

MONTHS: list[str] = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
]

DAYS_IN_MONTH: list[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

PROFILES: dict[str, dict] = {
    "Actif (peu présent la journée)": {"day_ratio": 0.25, "evening_ratio": 0.75},
    "Retraité (présent la journée)": {"day_ratio": 0.55, "evening_ratio": 0.45},
    "Avec enfants scolarisés": {"day_ratio": 0.50, "evening_ratio": 0.50},
}

BATTERY_MODELS: dict[str, dict] = {
    "Élite (4,8 kWh)": {"capacity_wh": 4800, "label": "Élite"},
    "Prestige (10,65 kWh)": {"capacity_wh": 10650, "label": "Prestige"},
    "Maestro (14,3 kWh)": {"capacity_wh": 14336, "label": "Maestro"},
}

# Tranches marginales NC (Code des impôts NC)
TRANCHES_NC: list[dict] = [
    {"taux": 0,  "label": "Non imposable", "desc": "0%"},
    {"taux": 15, "label": "Tranche 15%",   "desc": "15%"},
    {"taux": 25, "label": "Tranche 25%",   "desc": "25%"},
    {"taux": 30, "label": "Tranche 30%",   "desc": "30%"},
    {"taux": 40, "label": "Tranche 40%",   "desc": "> 5 388 000 XPF"},
]

BATTERY_DOD: float = 0.85
POOL_EXTRA_KWH: float = 350.0

DEFAULTS: dict = {
    "tarif_dom_low": 37.91,
    "tarif_dom_high": 42.24,
    "tarif_pro": 29.62,
    "revente_high": 21.0,
    "revente_std": 15.0,
    "prime_fixe": 608.42,
    "taxe_communale": 9.0,
    "redevance_comptage": 703.0,
    "tgc": 3.0,
    "ensoleillement": 4.2,
    "pertes": 15.0,
    "hausse_tarif": 5.0,
    "duree_vie": 25,
    "duree_bat": 10,
    "deduction_plafond": 1_000_000,
    "cout_pv_resid": 350.0,
    "cout_pv_pro": 300.0,
    "cout_batterie": 85_000.0,
}

# ===================== COULEURS =====================

ORANGE = "#F07020"
ORANGE_GLOW = "rgba(240,112,32,0.4)"
ORANGE_SOFT = "rgba(240,112,32,0.15)"
ANTHRACITE = "#1A1A2E"
DARK2 = "#16213E"
DARK3 = "#0F3460"
BLANC = "#FFFFFF"
GREEN = "#00D4A0"
GREEN_SOFT = "rgba(0,212,160,0.15)"
RED = "#FF4B6E"
BLUE = "#4FC3F7"

# ===================== CHARGEMENT LOGO =====================

def load_logo_b64() -> str:
    """Charge le logo Solar Concept en base64.

    Returns:
        Data URI base64 du logo, ou chaîne vide si non trouvé.
    """
    candidates = [
        Path(__file__).parent / "Données" / "Graphique" / "LOGO SC ORANGE.png",
        Path(__file__).parent / "Données" / "Graphique" / "Logo Orange Gros.png",
        Path(__file__).parent / "Données" / "Graphique" / "LOGO-230x230.png",
    ]
    for p in candidates:
        if p.exists():
            with open(p, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return ""


LOGO_B64 = load_logo_b64()

# ===================== CSS SOLAR 2030 =====================

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700;800&family=Rajdhani:wght@600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif;
    background: {ANTHRACITE};
    color: #E8E8F0;
}}

/* ---- SCROLLBAR ---- */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {DARK2}; }}
::-webkit-scrollbar-thumb {{ background: {ORANGE}; border-radius: 3px; }}

/* ---- HEADER ---- */
.brand-header {{
    background: linear-gradient(135deg, {DARK2} 0%, {DARK3} 100%);
    padding: 1rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(240,112,32,0.3);
    box-shadow: 0 0 40px rgba(240,112,32,0.15), inset 0 1px 0 rgba(255,255,255,0.05);
    position: relative;
    overflow: hidden;
}}
.brand-header::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(240,112,32,0.12) 0%, transparent 70%);
    pointer-events: none;
}}
.brand-logo-img {{
    height: 52px;
    width: auto;
    object-fit: contain;
    filter: drop-shadow(0 0 8px rgba(240,112,32,0.5));
}}
.brand-title {{
    color: {ORANGE};
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-shadow: 0 0 20px rgba(240,112,32,0.6);
}}
.brand-slogan {{
    color: rgba(255,255,255,0.5);
    font-size: 0.78rem;
    letter-spacing: 1px;
    margin-top: 2px;
}}
.brand-tel {{
    color: {ORANGE};
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-shadow: 0 0 12px rgba(240,112,32,0.5);
}}
.btn-print-header {{
    background: rgba(240,112,32,0.15);
    border: 1px solid rgba(240,112,32,0.5);
    color: {ORANGE};
    padding: 8px 18px;
    border-radius: 8px;
    cursor: pointer;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.2s;
    text-transform: uppercase;
}}
.btn-print-header:hover {{
    background: {ORANGE};
    color: white;
    box-shadow: 0 0 20px rgba(240,112,32,0.5);
}}

/* ---- CARTES RÉSULTATS ---- */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 1.2rem;
}}
.kpi-card {{
    background: linear-gradient(135deg, rgba(22,33,62,0.8) 0%, rgba(15,52,96,0.4) 100%);
    border: 1px solid rgba(240,112,32,0.25);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    transition: border-color 0.2s, box-shadow 0.2s;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, {ORANGE}, transparent);
}}
.kpi-card:hover {{
    border-color: rgba(240,112,32,0.6);
    box-shadow: 0 0 20px rgba(240,112,32,0.15);
}}
.kpi-value {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: {ORANGE};
    text-shadow: 0 0 15px rgba(240,112,32,0.4);
    line-height: 1.1;
}}
.kpi-value.green {{ color: {GREEN}; text-shadow: 0 0 15px rgba(0,212,160,0.4); }}
.kpi-value.red {{ color: {RED}; text-shadow: 0 0 15px rgba(255,75,110,0.4); }}
.kpi-value.blue {{ color: {BLUE}; text-shadow: 0 0 15px rgba(79,195,247,0.4); }}
.kpi-label {{
    font-size: 0.72rem;
    color: rgba(255,255,255,0.45);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 4px;
    font-weight: 600;
}}

/* ---- TITRES SECTION ---- */
.sec-title {{
    color: {ORANGE};
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    border-left: 3px solid {ORANGE};
    padding-left: 10px;
    margin: 1.4rem 0 0.8rem;
    text-shadow: 0 0 12px rgba(240,112,32,0.4);
}}

/* ---- STREAMLIT OVERRIDES ---- */
div[data-testid="stTabs"] button[data-baseweb="tab"] {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
    color: rgba(255,255,255,0.5) !important;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
    color: {ORANGE} !important;
    border-bottom-color: {ORANGE} !important;
}}
div[data-testid="stTabs"] {{
    border-bottom: 1px solid rgba(240,112,32,0.2);
}}
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] > div,
div[data-testid="stTextInput"] input {{
    background: rgba(22,33,62,0.8) !important;
    border: 1px solid rgba(240,112,32,0.25) !important;
    color: #E8E8F0 !important;
    border-radius: 8px !important;
}}
div[data-testid="stCheckbox"] {{
    color: #E8E8F0;
}}
div[data-testid="stSlider"] > div > div > div {{
    background: {ORANGE} !important;
}}
.stButton > button {{
    background: linear-gradient(135deg, {ORANGE} 0%, #D45A10 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0.6rem 1.2rem;
    box-shadow: 0 4px 20px rgba(240,112,32,0.4);
    transition: all 0.2s;
}}
.stButton > button:hover {{
    box-shadow: 0 6px 30px rgba(240,112,32,0.6);
    transform: translateY(-1px);
}}
div[data-testid="stMetric"] {{
    background: rgba(22,33,62,0.6);
    border-radius: 10px;
    padding: 0.6rem;
    border: 1px solid rgba(240,112,32,0.2);
}}
.stInfo {{
    background: rgba(79,195,247,0.1) !important;
    border: 1px solid rgba(79,195,247,0.3) !important;
    border-radius: 8px;
    color: {BLUE} !important;
}}

/* ---- DATAFRAME ---- */
div[data-testid="stDataFrame"] {{
    border: 1px solid rgba(240,112,32,0.2);
    border-radius: 10px;
    overflow: hidden;
}}

/* ---- ALERTE DÉDUCTION ---- */
.deduction-alert {{
    background: linear-gradient(135deg, rgba(240,112,32,0.1), rgba(240,112,32,0.05));
    border: 1px solid rgba(240,112,32,0.4);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.8);
}}
.deduction-alert strong {{ color: {ORANGE}; }}

/* ===================== PRINT ===================== */
@media print {{
    html, body {{
        background: white !important;
        color: black !important;
        font-size: 11pt;
    }}
    .brand-header {{
        background: #1A1A2E !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        border-radius: 8px;
        margin-bottom: 12px;
    }}
    .kpi-card {{
        background: #f8f8f8 !important;
        border: 1px solid #ddd !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        break-inside: avoid;
    }}
    .kpi-value {{ color: #F07020 !important; text-shadow: none !important; }}
    .kpi-value.green {{ color: #00A070 !important; }}
    .kpi-value.red {{ color: #CC0000 !important; }}
    .sec-title {{ color: #F07020 !important; border-left-color: #F07020 !important; }}
    .stButton, button {{ display: none !important; }}
    div[data-testid="stTabs"] {{ display: none !important; }}
    .no-print {{ display: none !important; }}
}}
</style>
"""

# ===================== UTILITAIRES =====================

def fmt(n: float) -> str:
    """Formate un nombre entier en locale française."""
    return f"{int(round(n)):,}".replace(",", "\u00a0")


def fmt_dec(n: float, decimals: int = 1) -> str:
    """Formate un nombre décimal en locale française."""
    return f"{n:,.{decimals}f}".replace(",", "\u00a0").replace(".", ",")


def get_settings() -> dict:
    """Retourne les paramètres depuis st.session_state ou les valeurs par défaut."""
    return {k: st.session_state.get(f"param_{k}", v) for k, v in DEFAULTS.items()}


@lru_cache(maxsize=64)
def production_mensuelle(kwc: float, ensoleillement: float, pertes: float) -> tuple[float, ...]:
    """Calcule la production mensuelle PV.

    Args:
        kwc: Puissance crête installée en kWc.
        ensoleillement: Irradiance moyenne Nouméa kWh/kWc/jour.
        pertes: Pertes système en %.

    Returns:
        Tuple de 12 productions mensuelles en kWh.
    """
    factor = 1 - pertes / 100
    return tuple(
        kwc * ensoleillement * SOLAR_FACTORS[i] * factor * DAYS_IN_MONTH[i]
        for i in range(12)
    )


def calc_facture_mois(
    conso: float,
    autoconso: float,
    prod: float,
    settings: dict,
    tranche_haute: bool = False,
) -> float:
    """Calcule la facture mensuelle résidentielle DOM.

    Args:
        conso: Consommation mensuelle kWh.
        autoconso: Autoconsommation PV mensuelle kWh.
        prod: Production PV mensuelle kWh.
        settings: Paramètres financiers.
        tranche_haute: Tarif haute tranche.

    Returns:
        Montant facture XPF.
    """
    s = settings
    tarif = s["tarif_dom_high"] if tranche_haute else s["tarif_dom_low"]
    tgc = s["tgc"] / 100
    achat = max(0.0, conso - autoconso)
    surplus = max(0.0, prod - autoconso)
    revente = surplus * s["revente_high"]
    energie = achat * tarif * (1 + tgc)
    return energie + s["prime_fixe"] + s["taxe_communale"] + s["redevance_comptage"] - revente


def calc_deduction_fiscale(invest: float, taux_marginal: int, plafond_annuel: float) -> dict:
    """Calcule correctement la déduction fiscale NC.

    La déduction NC est un abattement sur le revenu imposable (Art. 5 bis Code impôts NC).
    L'économie réelle = montant_déductible × taux_marginal_imposition.
    Le plafond de déduction s'applique sur le MONTANT DÉDUCTIBLE (pas sur l'économie).

    Args:
        invest: Investissement total en XPF.
        taux_marginal: Taux marginal d'imposition NC en % (0, 15, 25, 30 ou 40).
        plafond_annuel: Plafond de déduction annuel en XPF.

    Returns:
        Dict avec 'deduction_totale', 'economies_fiscales_totales', 'nb_annees', 'detail'.
    """
    # Montant total déductible = 100% de l'investissement (équipements éligibles NC)
    montant_deductible = invest
    nb_annees = math.ceil(montant_deductible / plafond_annuel) if plafond_annuel > 0 else 0
    nb_annees = min(nb_annees, 5)  # Plafond pratique NC = 5 ans max

    detail = []
    restant = montant_deductible
    for y in range(1, nb_annees + 1):
        deduc_an = min(restant, plafond_annuel)
        eco_an = deduc_an * taux_marginal / 100
        detail.append({"annee": y, "deduction": deduc_an, "economie_fiscale": eco_an})
        restant -= deduc_an
        if restant <= 0:
            break

    economies_totales = sum(d["economie_fiscale"] for d in detail)
    return {
        "deduction_totale": montant_deductible,
        "economies_fiscales_totales": economies_totales,
        "nb_annees": len(detail),
        "detail": detail,
    }


def build_amort_table(
    invest: float,
    economie_annuelle: float,
    hausse_tarif: float,
    duree: int,
    taux_marginal: int,
    plafond_deduction: float,
    cout_batterie_remplacement: float = 0.0,
    annee_remplacement: int = 0,
) -> pd.DataFrame:
    """Construit le tableau d'amortissement sur la durée de vie.

    Correction v2.0 : La déduction fiscale NC = abattement revenu × taux marginal.
    Le plafond s'applique sur le montant déductible annuel, pas sur l'économie fiscale.

    Args:
        invest: Investissement initial en XPF.
        economie_annuelle: Économie annuelle de référence (année 1) en XPF.
        hausse_tarif: Taux de revalorisation annuel du tarif en %.
        duree: Durée d'amortissement en années.
        taux_marginal: Taux marginal NC en % (0, 15, 25, 30, 40).
        plafond_deduction: Plafond déductible annuel en XPF (paramétrable).
        cout_batterie_remplacement: Coût remplacement batterie en XPF.
        annee_remplacement: Année du remplacement batterie.

    Returns:
        DataFrame d'amortissement.
    """
    fiscal = calc_deduction_fiscale(invest, taux_marginal, plafond_deduction)

    rows = []
    cumul = -invest
    fiscal_detail = {d["annee"]: d["economie_fiscale"] for d in fiscal["detail"]}

    for y in range(1, duree + 1):
        eco = economie_annuelle * ((1 + hausse_tarif / 100) ** (y - 1))
        eco_fiscale = fiscal_detail.get(y, 0.0)
        remplacement = cout_batterie_remplacement if y == annee_remplacement else 0.0
        benefice_net = eco + eco_fiscale - remplacement
        cumul += benefice_net

        rows.append({
            "An": f"An {y}",
            "Économie énergie (XPF)": int(round(eco)),
            "Économie fiscale NC (XPF)": int(round(eco_fiscale)),
            "Remplacement batterie (XPF)": int(round(remplacement)),
            "Bénéfice net (XPF)": int(round(benefice_net)),
            "Cumul (XPF)": int(round(cumul)),
        })

    return pd.DataFrame(rows)


# ===================== GRAPHIQUES SOLAR 2030 =====================

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(22,33,62,0.4)",
    font=dict(family="Space Grotesk", color="#C8C8D8", size=12),
    margin=dict(t=50, b=60, l=10, r=10),
    height=340,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.35,
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    ),
)


def chart_sankey_energie(
    prod_annuelle: float,
    autoconso_an: float,
    surplus_an: float,
    achat_an: float,
    conso_an: float,
) -> go.Figure:
    """Diagramme Sankey du flux énergétique annuel.

    Args:
        prod_annuelle: Production PV totale kWh/an.
        autoconso_an: Autoconsommation kWh/an.
        surplus_an: Surplus réinjecté réseau kWh/an.
        achat_an: Achat réseau kWh/an.
        conso_an: Consommation totale kWh/an.

    Returns:
        Figure Plotly Sankey.
    """
    # Noeuds : 0=Soleil, 1=PV, 2=Autoconso, 3=Surplus, 4=Réseau, 5=Conso maison
    labels = ["☀️ Soleil", "⚡ PV", "🏠 Autoconso.", "↩️ Réseau", "🔌 EEC", "⚡ Conso. totale"]
    colors_node = [ORANGE, "#FFB347", GREEN, BLUE, "#FF6B6B", "#E8E8F0"]
    source = [0, 1, 1, 4]
    target = [1, 2, 3, 5]
    value_link = [prod_annuelle, autoconso_an, surplus_an, achat_an]
    # Conso totale = autoconso + achat => flux vers conso totale
    source = [0, 1, 1, 4, 2, 4]
    target = [1, 2, 3, 5, 5, 5]
    value_link = [prod_annuelle, autoconso_an, surplus_an, achat_an, autoconso_an, achat_an]
    # Simplifié : montrer flux direct
    source = [0, 1, 1, 4]
    target = [1, 2, 3, 2]
    value_link = [prod_annuelle, autoconso_an, max(1.0, surplus_an), achat_an]
    labels = ["☀️ Soleil", "⚡ PV", "🏠 Autoconso + EEC", "↩️ Surplus réseau", "🔌 EEC"]
    source = [0, 1, 1, 4]
    target = [1, 2, 3, 2]
    value_link = [prod_annuelle, autoconso_an, max(1.0, surplus_an), achat_an]
    colors_node = [ORANGE, "#FFB347", GREEN, BLUE, "#FF6B6B"]
    colors_link = [
        "rgba(240,112,32,0.4)",
        "rgba(0,212,160,0.4)",
        "rgba(79,195,247,0.4)",
        "rgba(255,107,107,0.4)",
    ]
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color="rgba(255,255,255,0.1)", width=0.5),
            label=labels,
            color=colors_node,
            hovertemplate="%{label}: %{value:.0f} kWh<extra></extra>",
        ),
        link=dict(
            source=source,
            target=target,
            value=value_link,
            color=colors_link,
        ),
    ))
    fig.update_layout(
        title=dict(text="Flux énergétique annuel", font=dict(color=ORANGE, size=14, family="Rajdhani")),
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("legend",)},
        height=360,
    )
    return fig


def chart_area_mensuel(
    autoconso_monthly: list[float],
    surplus_monthly: list[float],
    achat_monthly: list[float],
    prod_monthly: list[float],
    title: str = "Flux énergétique mensuel (kWh)",
) -> go.Figure:
    """Area chart gradient pour la répartition mensuelle.

    Remplace les barres empilées par des courbes d'aire superposées.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MONTHS, y=[round(a) for a in achat_monthly],
        name="Achat réseau", fill="tozeroy",
        fillcolor="rgba(255,75,110,0.25)",
        line=dict(color=RED, width=2),
        mode="lines",
        hovertemplate="<b>%{x}</b><br>Achat réseau : %{y} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=MONTHS, y=[round(a) for a in autoconso_monthly],
        name="Autoconsommation PV", fill="tozeroy",
        fillcolor="rgba(240,112,32,0.3)",
        line=dict(color=ORANGE, width=2.5),
        mode="lines",
        hovertemplate="<b>%{x}</b><br>Autoconso : %{y} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=MONTHS, y=[round(p) for p in prod_monthly],
        name="Production PV totale",
        line=dict(color="#FFD700", width=2, dash="dot"),
        mode="lines+markers",
        marker=dict(size=5, color=ORANGE),
        hovertemplate="<b>%{x}</b><br>Production : %{y} kWh<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=ORANGE, size=13, family="Rajdhani")),
        xaxis=dict(showgrid=False, color="#666"),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            color="#666",
            title="kWh",
        ),
        **PLOTLY_LAYOUT,
    )
    return fig


def chart_gauge_autoconso(taux: float) -> go.Figure:
    """Jauge de taux d'autoconsommation.

    Args:
        taux: Taux d'autoconsommation en %.

    Returns:
        Figure Plotly gauge.
    """
    color = ORANGE if taux < 60 else GREEN if taux >= 80 else "#FFD700"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(taux, 1),
        number=dict(suffix="%", font=dict(size=32, color=color, family="Rajdhani")),
        delta=dict(reference=70, valueformat=".1f", suffix="% vs cible 70%"),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#555", tickfont=dict(color="#888")),
            bar=dict(color=color, thickness=0.3),
            bgcolor="rgba(22,33,62,0.6)",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(255,75,110,0.15)"),
                dict(range=[40, 70], color="rgba(255,215,0,0.12)"),
                dict(range=[70, 100], color="rgba(0,212,160,0.15)"),
            ],
            threshold=dict(
                line=dict(color="#FFD700", width=2),
                thickness=0.8,
                value=70,
            ),
        ),
        title=dict(text="Taux d'autoconsommation", font=dict(color=ORANGE, size=13, family="Rajdhani")),
    ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("legend", "height")},
        height=260,
        margin=dict(t=60, b=20, l=30, r=30),
    )
    return fig


def chart_waterfall_amort(
    invest: float,
    df_amort: pd.DataFrame,
    payback_year: int | None,
) -> go.Figure:
    """Waterfall chart pour l'amortissement cumulé.

    Chaque barre = bénéfice net annuel. Le cumul apparaît clairement.

    Args:
        invest: Investissement initial.
        df_amort: DataFrame d'amortissement.
        payback_year: Année de retour sur investissement.

    Returns:
        Figure Plotly waterfall.
    """
    years = ["Invest."] + df_amort["An"].tolist()
    measures = ["absolute"] + ["relative"] * len(df_amort)
    y_values = [-invest] + df_amort["Bénéfice net (XPF)"].tolist()
    text_values = [f"-{fmt(invest)}"] + [
        f"+{fmt(v)}" if v >= 0 else f"{fmt(v)}" for v in df_amort["Bénéfice net (XPF)"].tolist()
    ]

    colors = []
    for i, row in df_amort.iterrows():
        if payback_year and int(str(row["An"]).split()[1]) == payback_year:
            colors.append(GREEN)
        elif row["Bénéfice net (XPF)"] > 0:
            colors.append(f"rgba(0,212,160,0.8)")
        else:
            colors.append(f"rgba(255,75,110,0.8)")

    fig = go.Figure(go.Waterfall(
        name="Bilan",
        orientation="v",
        measure=measures,
        x=years,
        y=y_values,
        text=text_values,
        textposition="outside",
        textfont=dict(size=9, color="#aaa"),
        connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1, dash="dot")),
        increasing=dict(marker=dict(color=f"rgba(0,212,160,0.8)", line=dict(color=GREEN, width=1))),
        decreasing=dict(marker=dict(color=f"rgba(255,75,110,0.8)", line=dict(color=RED, width=1))),
        totals=dict(marker=dict(color=ORANGE, line=dict(color=ORANGE, width=1))),
    ))
    # Ligne zéro
    fig.add_hline(y=0, line=dict(color=ORANGE, width=1, dash="dash"), opacity=0.5)
    fig.update_layout(
        title=dict(text="Waterfall — Bilan cumulé année par année (XPF)", font=dict(color=ORANGE, size=13, family="Rajdhani")),
        xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=9)),
        showlegend=False,
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("legend", "height")},
        height=400,
        margin=dict(t=60, b=100, l=10, r=10),
    )
    return fig


def chart_scatter_roi(df_amort: pd.DataFrame, invest: float) -> go.Figure:
    """Scatter plot futuriste des économies cumulées vs investissement.

    Args:
        df_amort: DataFrame d'amortissement.
        invest: Investissement initial.

    Returns:
        Figure Plotly scatter avec gradient.
    """
    years = [int(r.split()[1]) for r in df_amort["An"]]
    cumuls = df_amort["Cumul (XPF)"].tolist()
    payback_y = next((y for y, c in zip(years, cumuls) if c >= 0), None)

    fig = go.Figure()
    # Zone de perte
    fig.add_hrect(y0=min(cumuls) * 1.1, y1=0, fillcolor="rgba(255,75,110,0.06)", line_width=0)
    # Zone de gain
    fig.add_hrect(y0=0, y1=max(cumuls) * 1.1, fillcolor="rgba(0,212,160,0.06)", line_width=0)
    # Ligne investissement
    fig.add_hline(y=0, line=dict(color="#666", width=1, dash="dash"))

    # Courbe cumul avec gradient par couleur
    fig.add_trace(go.Scatter(
        x=years, y=cumuls,
        mode="lines+markers",
        name="Bilan cumulé",
        line=dict(color=ORANGE, width=2.5, shape="spline"),
        marker=dict(
            size=6,
            color=cumuls,
            colorscale=[[0, RED], [0.5, ORANGE], [1, GREEN]],
            showscale=False,
        ),
        fill="tozeroy",
        fillcolor="rgba(240,112,32,0.08)",
        hovertemplate="<b>An %{x}</b><br>Bilan : %{y:,.0f} XPF<extra></extra>",
    ))

    # Marqueur payback
    if payback_y:
        payback_val = cumuls[payback_y - 1]
        fig.add_trace(go.Scatter(
            x=[payback_y], y=[payback_val],
            mode="markers+text",
            name="Retour sur invest.",
            marker=dict(size=16, color=GREEN, symbol="star", line=dict(color=BLANC, width=1.5)),
            text=[f"✦ An {payback_y}"],
            textposition="top center",
            textfont=dict(color=GREEN, size=12, family="Rajdhani"),
        ))

    fig.update_layout(
        title=dict(text="Évolution du bilan cumulé (XPF)", font=dict(color=ORANGE, size=13, family="Rajdhani")),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            title="Années",
            color="#666",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            title="XPF",
            color="#666",
        ),
        **PLOTLY_LAYOUT,
    )
    return fig


# ===================== HEADER =====================

def render_header() -> None:
    """Affiche le header Solar Concept avec logo et bouton impression."""
    logo_html = f'<img src="{LOGO_B64}" class="brand-logo-img" alt="Solar Concept" />' if LOGO_B64 else ""
    print_btn = """
    <button class="btn-print-header" onclick="window.print()">
        🖨️ Imprimer / PDF
    </button>
    """
    st.markdown(f"""
    <div class="brand-header">
        <div style="display:flex;align-items:center;gap:16px;">
            {logo_html}
            <div>
                <div class="brand-title">Solar Concept</div>
                <div class="brand-slogan">Votre meilleure source d'énergie</div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:20px;">
            {print_btn}
            <div class="brand-tel">☎ 47 03 02</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpis(cards: list[dict]) -> None:
    """Affiche une rangée de KPI cards.

    Args:
        cards: Liste de dicts avec 'value', 'label', 'style' ('default'|'green'|'red'|'blue').
    """
    html = '<div class="kpi-grid">'
    for card in cards:
        style = card.get("style", "default")
        css_class = "" if style == "default" else style
        html += f"""
        <div class="kpi-card">
            <div class="kpi-value {css_class}">{card['value']}</div>
            <div class="kpi-label">{card['label']}</div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def section(title: str) -> None:
    """Affiche un titre de section Solar 2030."""
    st.markdown(f'<div class="sec-title">{title}</div>', unsafe_allow_html=True)


def render_deduction_info(invest: float, taux_marginal: int, plafond: float) -> None:
    """Affiche le détail de la déduction fiscale NC.

    Args:
        invest: Investissement total.
        taux_marginal: Taux marginal d'imposition.
        plafond: Plafond annuel déductible.
    """
    if taux_marginal == 0:
        st.markdown("""
        <div class="deduction-alert">
            ℹ️ Tranche <strong>non imposable</strong> — aucune économie fiscale calculée.
        </div>""", unsafe_allow_html=True)
        return
    fiscal = calc_deduction_fiscale(invest, taux_marginal, plafond)
    st.markdown(f"""
    <div class="deduction-alert">
        🧾 <strong>Déduction fiscale NC</strong> (abattement revenu imposable) :<br>
        Montant déductible : <strong>{fmt(fiscal['deduction_totale'])} XPF</strong>
        (étalé sur <strong>{fiscal['nb_annees']} an(s)</strong>, plafond {fmt(plafond)} XPF/an)<br>
        Économie fiscale totale à <strong>{taux_marginal}%</strong> :
        <strong style="color:#F07020;">{fmt(fiscal['economies_fiscales_totales'])} XPF</strong>
    </div>""", unsafe_allow_html=True)


def tranche_selector(key: str) -> int:
    """Widget de sélection de tranche marginale NC.

    Args:
        key: Clé Streamlit unique.

    Returns:
        Taux marginal sélectionné en %.
    """
    options = [f"{t['taux']}% — {t['label']}" for t in TRANCHES_NC]
    idx = st.selectbox("Tranche marginale d'imposition NC", options, index=0, key=key)
    return TRANCHES_NC[options.index(idx)]["taux"]


# ===================== ONGLET 1 — INSTALLATION COMPLÈTE =====================

def tab_installation_complete(s: dict) -> None:
    """Onglet 1 : Dimensionnement PV à partir de la consommation annuelle."""
    col1, col2 = st.columns([2, 1])
    with col1:
        conso_an = st.number_input("Consommation annuelle (kWh)", min_value=100.0, max_value=100000.0, value=4500.0, step=100.0, key="c1_conso")
        piscine = st.checkbox("Piscine (+350 kWh/mois)", key="c1_piscine")
        profil = st.selectbox("Profil d'occupation", list(PROFILES.keys()), key="c1_profil")
        kwc = st.number_input("Puissance PV (kWc)", min_value=0.5, max_value=500.0, value=3.0, step=0.5, key="c1_kwc")
    with col2:
        batterie = st.selectbox("Batterie", ["Aucune"] + list(BATTERY_MODELS.keys()), key="c1_bat")
        pv_wc = st.number_input("Puissance unitaire panneau (Wc)", min_value=100, max_value=700, value=400, step=10, key="c1_wpanneau")
        taux_marginal = tranche_selector("c1_tranche_fisc")
        tranche_haute = st.checkbox("Tranche haute EEC (> 500 kWh/mois)", key="c1_tranche")

    if not st.button("⚡ Calculer", key="btn1", type="primary", use_container_width=True):
        return

    if piscine:
        conso_an += POOL_EXTRA_KWH * 12

    profil_data = PROFILES[profil]
    day_ratio = profil_data["day_ratio"]

    prod_monthly = list(production_mensuelle(kwc, s["ensoleillement"], s["pertes"]))
    prod_annuelle = sum(prod_monthly)

    conso_monthly = [conso_an * d / sum(DAYS_IN_MONTH) for d in DAYS_IN_MONTH]
    conso_jour = [c * day_ratio for c in conso_monthly]

    autoconso_monthly = [min(p, cj) for p, cj in zip(prod_monthly, conso_jour)]
    surplus_monthly = [p - a for p, a in zip(prod_monthly, autoconso_monthly)]
    achat_monthly = [c - a for c, a in zip(conso_monthly, autoconso_monthly)]

    autoconso_an = sum(autoconso_monthly)
    surplus_an = sum(surplus_monthly)
    achat_an = sum(achat_monthly)
    taux_autoconso = autoconso_an / prod_annuelle * 100

    nb_panneaux = -(-int(kwc * 1000) // pv_wc)
    surface = nb_panneaux * 2

    facture_sans = sum(calc_facture_mois(conso_monthly[i], 0, 0, s, tranche_haute) for i in range(12))
    facture_avec = sum(
        calc_facture_mois(conso_monthly[i], autoconso_monthly[i], prod_monthly[i], s, tranche_haute)
        for i in range(12)
    )
    economie_an = facture_sans - facture_avec

    invest = kwc * 1000 * s["cout_pv_resid"]
    bat_data = BATTERY_MODELS.get(batterie)
    invest_bat = 0.0
    bat_label = ""
    if bat_data:
        invest_bat = bat_data["capacity_wh"] / 1000 * s["cout_batterie"]
        bat_label = f"{bat_data['label']} ({bat_data['capacity_wh']/1000:.1f} kWh)"
        invest += invest_bat

    section("Installation")
    render_kpis([
        {"value": f"{fmt_dec(kwc)} kWc", "label": "Puissance PV"},
        {"value": str(nb_panneaux), "label": f"Panneaux — {surface} m²"},
        {"value": f"{fmt(round(prod_annuelle))} kWh", "label": "Production / an"},
        {"value": f"{fmt_dec(taux_autoconso)}%", "label": "Autoconsommation"},
    ])

    section("Finances")
    render_kpis([
        {"value": f"{fmt(invest)} XPF", "label": "Investissement total", "style": "blue"},
        {"value": f"{fmt(facture_sans)} XPF", "label": "Facture sans PV / an", "style": "red"},
        {"value": f"{fmt(facture_avec)} XPF", "label": "Facture avec PV / an", "style": "green"},
        {"value": f"{fmt(economie_an)} XPF", "label": "Économie annuelle", "style": "green"},
    ])
    if bat_label:
        st.info(f"🔋 Batterie : **{bat_label}** — {fmt(invest_bat)} XPF")

    render_deduction_info(invest, taux_marginal, s["deduction_plafond"])

    # Graphiques
    col_g1, col_g2 = st.columns([3, 2])
    with col_g1:
        st.plotly_chart(
            chart_area_mensuel(autoconso_monthly, surplus_monthly, achat_monthly, prod_monthly),
            use_container_width=True,
        )
    with col_g2:
        st.plotly_chart(chart_gauge_autoconso(taux_autoconso), use_container_width=True)

    st.plotly_chart(
        chart_sankey_energie(prod_annuelle, autoconso_an, surplus_an, achat_an, conso_an),
        use_container_width=True,
    )

    annee_remplacement = s["duree_bat"] if bat_data else 0
    cout_remplacement = invest_bat if bat_data else 0.0

    df = build_amort_table(
        invest, economie_an, s["hausse_tarif"], s["duree_vie"],
        taux_marginal, s["deduction_plafond"], cout_remplacement, annee_remplacement,
    )
    payback = next((int(r["An"].split()[1]) for _, r in df.iterrows() if r["Cumul (XPF)"] >= 0), None)

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.plotly_chart(chart_waterfall_amort(invest, df, payback), use_container_width=True)
    with col_w2:
        st.plotly_chart(chart_scatter_roi(df, invest), use_container_width=True)

    if payback:
        render_kpis([{"value": f"An {payback}", "label": "Retour sur investissement", "style": "green"}])

    section("Tableau d'amortissement")

    def highlight_payback(row: pd.Series) -> list[str]:
        if row["Cumul (XPF)"] >= 0:
            return ["background-color: rgba(0,212,160,0.1); color: #00D4A0; font-weight: bold"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_payback, axis=1).format(
            {col: lambda x: fmt(x) for col in df.columns if "(XPF)" in col}
        ),
        use_container_width=True,
        hide_index=True,
    )


# ===================== ONGLET 2 — BATTERIE + DONNÉES COMPLÈTES =====================

def tab_batterie_donnees_completes(s: dict) -> None:
    """Onglet 2 : Optimisation batterie avec relevés mensuels complets."""
    st.markdown("**Relevés de consommation mensuelle (kWh)**")
    col_inputs = st.columns(6)
    conso_monthly_input: list[float] = []
    for i, month in enumerate(MONTHS):
        with col_inputs[i % 6]:
            val = st.number_input(month, min_value=0.0, max_value=5000.0, value=375.0, step=10.0, key=f"c2_m{i}")
            conso_monthly_input.append(val)

    col1, col2 = st.columns(2)
    with col1:
        kwc = st.number_input("Puissance PV (kWc)", min_value=0.5, max_value=500.0, value=3.0, step=0.5, key="c2_kwc")
        batterie = st.selectbox("Modèle batterie", list(BATTERY_MODELS.keys()), key="c2_bat")
        pv_wc = st.number_input("Puissance panneau (Wc)", min_value=100, max_value=700, value=400, step=10, key="c2_wpanneau")
    with col2:
        profil = st.selectbox("Profil d'occupation", list(PROFILES.keys()), key="c2_profil")
        taux_marginal = tranche_selector("c2_tranche_fisc")
        tranche_haute = st.checkbox("Tranche haute EEC", key="c2_tranche")

    if not st.button("⚡ Calculer", key="btn2", type="primary", use_container_width=True):
        return

    profil_data = PROFILES[profil]
    day_ratio = profil_data["day_ratio"]

    prod_monthly = list(production_mensuelle(kwc, s["ensoleillement"], s["pertes"]))
    prod_annuelle = sum(prod_monthly)

    bat_data = BATTERY_MODELS[batterie]
    bat_kwh = bat_data["capacity_wh"] / 1000 * BATTERY_DOD

    conso_jour = [c * day_ratio for c in conso_monthly_input]
    autoconso_pv = [min(p, cj) for p, cj in zip(prod_monthly, conso_jour)]
    surplus_apres_jour = [p - a for p, a in zip(prod_monthly, autoconso_pv)]
    conso_soir = [c * (1 - day_ratio) for c in conso_monthly_input]
    autoconso_bat = [min(max(0.0, s_), cs) for s_, cs in zip(surplus_apres_jour, conso_soir)]
    autoconso_monthly = [pv + b for pv, b in zip(autoconso_pv, autoconso_bat)]
    surplus_monthly = [p - a for p, a in zip(prod_monthly, autoconso_monthly)]
    achat_monthly = [c - a for c, a in zip(conso_monthly_input, autoconso_monthly)]

    autoconso_an = sum(autoconso_monthly)
    surplus_an = sum(surplus_monthly)
    achat_an = sum(achat_monthly)
    taux_autoconso = autoconso_an / prod_annuelle * 100
    conso_an = sum(conso_monthly_input)

    nb_panneaux = -(-int(kwc * 1000) // pv_wc)
    invest_pv = kwc * 1000 * s["cout_pv_resid"]
    invest_bat = bat_kwh / BATTERY_DOD * s["cout_batterie"]
    invest_total = invest_pv + invest_bat

    facture_sans = sum(calc_facture_mois(conso_monthly_input[i], 0, 0, s, tranche_haute) for i in range(12))
    facture_avec = sum(
        calc_facture_mois(conso_monthly_input[i], autoconso_monthly[i], prod_monthly[i], s, tranche_haute)
        for i in range(12)
    )
    economie_an = facture_sans - facture_avec

    section("Installation")
    render_kpis([
        {"value": f"{fmt_dec(kwc)} kWc", "label": "Puissance PV"},
        {"value": str(nb_panneaux), "label": "Panneaux"},
        {"value": f"{fmt(round(prod_annuelle))} kWh", "label": "Production / an"},
        {"value": f"{fmt_dec(taux_autoconso)}%", "label": "Autoconso. avec batterie"},
    ])
    section("Finances")
    render_kpis([
        {"value": f"{fmt(invest_total)} XPF", "label": f"Invest. total (bat. {fmt(invest_bat)} XPF)", "style": "blue"},
        {"value": f"{fmt(facture_sans)} XPF", "label": "Facture sans PV / an", "style": "red"},
        {"value": f"{fmt(facture_avec)} XPF", "label": "Facture avec PV+bat. / an", "style": "green"},
        {"value": f"{fmt(economie_an)} XPF", "label": "Économie annuelle", "style": "green"},
    ])
    st.info(f"🔋 **{bat_data['label']}** — Capacité utile : **{fmt_dec(bat_kwh)} kWh** (DoD {int(BATTERY_DOD*100)}%)")
    render_deduction_info(invest_total, taux_marginal, s["deduction_plafond"])

    col_g1, col_g2 = st.columns([3, 2])
    with col_g1:
        st.plotly_chart(
            chart_area_mensuel(autoconso_monthly, surplus_monthly, achat_monthly, prod_monthly, "Flux mensuel avec batterie (kWh)"),
            use_container_width=True,
        )
    with col_g2:
        st.plotly_chart(chart_gauge_autoconso(taux_autoconso), use_container_width=True)

    st.plotly_chart(
        chart_sankey_energie(prod_annuelle, autoconso_an, surplus_an, achat_an, conso_an),
        use_container_width=True,
    )

    df = build_amort_table(
        invest_total, economie_an, s["hausse_tarif"], s["duree_vie"],
        taux_marginal, s["deduction_plafond"], invest_bat, s["duree_bat"],
    )
    payback = next((int(r["An"].split()[1]) for _, r in df.iterrows() if r["Cumul (XPF)"] >= 0), None)

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.plotly_chart(chart_waterfall_amort(invest_total, df, payback), use_container_width=True)
    with col_w2:
        st.plotly_chart(chart_scatter_roi(df, invest_total), use_container_width=True)

    section("Tableau d'amortissement")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ===================== ONGLET 3 — ESTIMATION BATTERIE =====================

def tab_estimation_batterie(s: dict) -> None:
    """Onglet 3 : Recommandation batterie avec données partielles."""
    col1, col2 = st.columns(2)
    with col1:
        conso_an = st.number_input("Consommation annuelle (kWh)", min_value=100.0, max_value=100000.0, value=4500.0, step=100.0, key="c3_conso")
        kwc = st.number_input("Puissance PV (kWc)", min_value=0.5, max_value=500.0, value=3.0, step=0.5, key="c3_kwc")
    with col2:
        profil = st.selectbox("Profil d'occupation", list(PROFILES.keys()), key="c3_profil")
        autonomie_nuit = st.slider("Couverture nuit souhaitée (%)", 0, 100, 50, key="c3_auto")

    if not st.button("⚡ Calculer", key="btn3", type="primary", use_container_width=True):
        return

    profil_data = PROFILES[profil]
    evening_ratio = 1 - profil_data["day_ratio"]

    prod_monthly = list(production_mensuelle(kwc, s["ensoleillement"], s["pertes"]))
    conso_monthly = [conso_an * d / sum(DAYS_IN_MONTH) for d in DAYS_IN_MONTH]
    conso_soir_monthly = [c * evening_ratio for c in conso_monthly]
    besoin_bat_kwh = max(conso_soir_monthly) * autonomie_nuit / 100

    recommande = None
    for model_name, model_data in BATTERY_MODELS.items():
        utile = model_data["capacity_wh"] / 1000 * BATTERY_DOD
        if utile >= besoin_bat_kwh:
            recommande = (model_name, model_data, utile)
            break
    if recommande is None:
        model_name, model_data = list(BATTERY_MODELS.items())[-1]
        utile = model_data["capacity_wh"] / 1000 * BATTERY_DOD
        recommande = (model_name, model_data, utile)

    bat_name, bat_data, bat_utile = recommande
    invest_bat = bat_data["capacity_wh"] / 1000 * s["cout_batterie"]
    invest_pv = kwc * 1000 * s["cout_pv_resid"]
    invest_total = invest_pv + invest_bat
    prod_annuelle = sum(prod_monthly)

    section("Recommandation batterie")
    render_kpis([
        {"value": bat_data["label"], "label": f"Modèle recommandé"},
        {"value": f"{fmt_dec(bat_utile)} kWh", "label": "Capacité utile"},
        {"value": f"{fmt_dec(besoin_bat_kwh)} kWh", "label": "Besoin estimé / nuit"},
        {"value": f"{fmt(invest_bat)} XPF", "label": "Investissement batterie", "style": "blue"},
    ])
    render_kpis([
        {"value": f"{fmt(invest_pv)} XPF", "label": "Investissement PV", "style": "blue"},
        {"value": f"{fmt(invest_total)} XPF", "label": "Investissement total", "style": "blue"},
        {"value": f"{fmt(round(prod_annuelle))} kWh", "label": "Production PV / an"},
        {"value": f"{fmt_dec(kwc)} kWc", "label": "Puissance PV"},
    ])

    # Radar comparatif modèles
    section("Comparatif modèles batterie")
    rows_bat = []
    for m_name, m_data in BATTERY_MODELS.items():
        utile = m_data["capacity_wh"] / 1000 * BATTERY_DOD
        cout = m_data["capacity_wh"] / 1000 * s["cout_batterie"]
        couverture = min(100.0, utile / max(besoin_bat_kwh, 0.001) * autonomie_nuit)
        rows_bat.append({
            "Modèle": m_name,
            "Cap. nominale (kWh)": f"{m_data['capacity_wh']/1000:.2f}",
            "Cap. utile (kWh)": f"{utile:.2f}",
            "Coût estimé (XPF)": fmt(cout),
            "Couverture nuit (%)": f"{couverture:.0f}%",
            "Recommandé": "⭐" if m_name == bat_name else "",
        })
    st.dataframe(pd.DataFrame(rows_bat), use_container_width=True, hide_index=True)

    # Area chart prod vs besoin soir
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MONTHS, y=[round(p) for p in prod_monthly],
        name="Production PV", fill="tozeroy",
        fillcolor="rgba(240,112,32,0.25)",
        line=dict(color=ORANGE, width=2.5),
        mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=MONTHS, y=[round(c) for c in conso_soir_monthly],
        name="Besoin soir", fill="tozeroy",
        fillcolor="rgba(255,75,110,0.2)",
        line=dict(color=RED, width=2, dash="dot"),
        mode="lines",
    ))
    fig.update_layout(
        title=dict(text="Production PV vs besoin soir mensuel (kWh)", font=dict(color=ORANGE, size=13, family="Rajdhani")),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)


# ===================== ONGLET 4 — ENTREPRISE HT =====================

def tab_entreprise(s: dict) -> None:
    """Onglet 4 : Calculs commerciaux en HT pour entreprises."""
    col1, col2 = st.columns(2)
    with col1:
        conso_an = st.number_input("Consommation annuelle HT (kWh)", min_value=100.0, value=20000.0, step=500.0, key="c4_conso")
        kwc = st.number_input("Puissance PV (kWc)", min_value=0.5, max_value=5000.0, value=20.0, step=1.0, key="c4_kwc")
        invest_ht = st.number_input("Investissement HT (XPF)", min_value=0.0, value=float(kwc * 1000 * s["cout_pv_pro"]), step=100000.0, key="c4_invest")
    with col2:
        pv_wc = st.number_input("Puissance panneau (Wc)", min_value=100, max_value=700, value=400, step=10, key="c4_wpanneau")
        tarif_ht = st.number_input("Tarif HT EEC (XPF/kWh)", min_value=1.0, value=s["tarif_pro"], step=0.5, key="c4_tarif")
        part_autoconso = st.slider("Part autoconsommée estimée (%)", 0, 100, 70, key="c4_autocons")
        revente_rate = st.number_input("Tarif revente réseau (XPF/kWh)", min_value=0.0, value=s["revente_std"], step=1.0, key="c4_revente")
        hausse = st.number_input("Revalorisation tarif (%/an)", min_value=0.0, value=s["hausse_tarif"], step=0.5, key="c4_hausse")

    if not st.button("⚡ Calculer", key="btn4", type="primary", use_container_width=True):
        return

    tgc = s["tgc"] / 100
    prod_monthly = list(production_mensuelle(kwc, s["ensoleillement"], s["pertes"]))
    prod_annuelle = sum(prod_monthly)
    conso_monthly = [conso_an * d / sum(DAYS_IN_MONTH) for d in DAYS_IN_MONTH]
    autoconso_monthly = [min(p * part_autoconso / 100, c) for p, c in zip(prod_monthly, conso_monthly)]
    surplus_monthly = [p - a for p, a in zip(prod_monthly, autoconso_monthly)]
    achat_monthly = [c - a for c, a in zip(conso_monthly, autoconso_monthly)]

    autoconso_an = sum(autoconso_monthly)
    surplus_an = sum(surplus_monthly)
    achat_an = sum(achat_monthly)
    taux_autoconso = autoconso_an / prod_annuelle * 100

    facture_sans = conso_an * tarif_ht * (1 + tgc)
    facture_avec = sum(achat_monthly) * tarif_ht * (1 + tgc) - surplus_an * revente_rate
    economie_an = facture_sans - facture_avec
    nb_panneaux = -(-int(kwc * 1000) // pv_wc)

    section("Installation entreprise")
    render_kpis([
        {"value": f"{fmt_dec(kwc)} kWc", "label": "Puissance PV"},
        {"value": str(nb_panneaux), "label": f"Panneaux — {nb_panneaux * 2} m²"},
        {"value": f"{fmt(round(prod_annuelle))} kWh", "label": "Production / an"},
        {"value": f"{fmt_dec(taux_autoconso)}%", "label": "Autoconsommation estimatif"},
    ])
    section("Finances HT")
    render_kpis([
        {"value": f"{fmt(invest_ht)} XPF", "label": "Investissement HT", "style": "blue"},
        {"value": f"{fmt(facture_sans)} XPF", "label": "Facture sans PV / an", "style": "red"},
        {"value": f"{fmt(facture_avec)} XPF", "label": "Facture avec PV / an", "style": "green"},
        {"value": f"{fmt(economie_an)} XPF", "label": "Économie annuelle HT", "style": "green"},
    ])

    col_g1, col_g2 = st.columns([3, 2])
    with col_g1:
        st.plotly_chart(
            chart_area_mensuel(autoconso_monthly, surplus_monthly, achat_monthly, prod_monthly, "Flux mensuel entreprise (kWh)"),
            use_container_width=True,
        )
    with col_g2:
        st.plotly_chart(chart_gauge_autoconso(taux_autoconso), use_container_width=True)

    st.plotly_chart(
        chart_sankey_energie(prod_annuelle, autoconso_an, surplus_an, achat_an, conso_an),
        use_container_width=True,
    )

    df = build_amort_table(invest_ht, economie_an, hausse, s["duree_vie"], 0, s["deduction_plafond"])
    payback = next((int(r["An"].split()[1]) for _, r in df.iterrows() if r["Cumul (XPF)"] >= 0), None)

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.plotly_chart(chart_waterfall_amort(invest_ht, df, payback), use_container_width=True)
    with col_w2:
        st.plotly_chart(chart_scatter_roi(df, invest_ht), use_container_width=True)

    section("Tableau d'amortissement HT")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ===================== ONGLET PARAMÈTRES =====================

def tab_parametres() -> None:
    """Onglet Paramètres : tarifs et hypothèses configurables."""
    st.markdown("### ⚙️ Paramètres techniques et financiers")
    st.caption("Modifiez les valeurs par défaut — pris en compte en temps réel sur tous les onglets.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="sec-title">Tarifs EEC résidentiel</div>', unsafe_allow_html=True)
        st.number_input("Tarif basse tranche DOM (XPF/kWh)", value=DEFAULTS["tarif_dom_low"], step=0.1, key="param_tarif_dom_low")
        st.number_input("Tarif haute tranche DOM (XPF/kWh)", value=DEFAULTS["tarif_dom_high"], step=0.1, key="param_tarif_dom_high")
        st.number_input("Tarif professionnel (XPF/kWh)", value=DEFAULTS["tarif_pro"], step=0.1, key="param_tarif_pro")
        st.number_input("Tarif revente haute (XPF/kWh)", value=DEFAULTS["revente_high"], step=0.5, key="param_revente_high")
        st.number_input("Tarif revente standard (XPF/kWh)", value=DEFAULTS["revente_std"], step=0.5, key="param_revente_std")
        st.number_input("Prime fixe mensuelle (XPF)", value=DEFAULTS["prime_fixe"], step=10.0, key="param_prime_fixe")
        st.number_input("Taxe communale (XPF/mois)", value=DEFAULTS["taxe_communale"], step=1.0, key="param_taxe_communale")
        st.number_input("Redevance comptage (XPF/mois)", value=DEFAULTS["redevance_comptage"], step=10.0, key="param_redevance_comptage")
        st.number_input("TGC (%)", value=DEFAULTS["tgc"], step=0.5, key="param_tgc")
    with col2:
        st.markdown(f'<div class="sec-title">Hypothèses techniques</div>', unsafe_allow_html=True)
        st.number_input("Irradiance Nouméa (kWh/kWc/jour)", value=DEFAULTS["ensoleillement"], step=0.1, key="param_ensoleillement")
        st.number_input("Pertes système (%)", value=DEFAULTS["pertes"], step=1.0, key="param_pertes")
        st.markdown(f'<div class="sec-title">Hypothèses financières</div>', unsafe_allow_html=True)
        st.number_input("Revalorisation tarif (%/an)", value=DEFAULTS["hausse_tarif"], step=0.5, key="param_hausse_tarif")
        st.number_input("Durée de vie PV (ans)", value=DEFAULTS["duree_vie"], step=1, key="param_duree_vie")
        st.number_input("Durée de vie batterie (ans)", value=DEFAULTS["duree_bat"], step=1, key="param_duree_bat")
        st.number_input(
            "Plafond déduction fiscale NC (XPF/an)",
            value=float(DEFAULTS["deduction_plafond"]),
            step=50000.0,
            key="param_deduction_plafond",
            help="Art. 5 bis Code impôts NC — plafond du montant annuel déductible du revenu imposable (≠ économie fiscale).",
        )
        st.markdown(f'<div class="sec-title">Coûts d\'installation</div>', unsafe_allow_html=True)
        st.number_input("Coût PV résidentiel (XPF/Wc)", value=DEFAULTS["cout_pv_resid"], step=10.0, key="param_cout_pv_resid")
        st.number_input("Coût PV professionnel (XPF/Wc)", value=DEFAULTS["cout_pv_pro"], step=10.0, key="param_cout_pv_pro")
        st.number_input("Coût batterie (XPF/kWh)", value=DEFAULTS["cout_batterie"], step=1000.0, key="param_cout_batterie")

    st.markdown("""
    <div class="deduction-alert" style="margin-top:1rem;">
        <strong>Rappel — Déduction fiscale NC :</strong><br>
        La déduction s'applique sur le revenu imposable (abattement), pas comme un crédit direct.
        L'économie réelle = montant déductible × taux marginal d'imposition.<br>
        Ex : investissement 3 000 000 XPF, plafond 1 000 000/an, tranche 30% →
        <strong>économie fiscale = 3 × 1 000 000 × 30% = 900 000 XPF sur 3 ans</strong>.
    </div>
    """, unsafe_allow_html=True)
    st.caption("Tarifs EEC 2024 — Nouméa, Nouvelle-Calédonie. Résultats estimatifs non contractuels.")


# ===================== MAIN =====================

def main() -> None:
    """Point d'entrée principal de l'application Streamlit."""
    st.set_page_config(
        page_title="Calculateur PV — Solar Concept",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    render_header()

    s = get_settings()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚡ Installation complète",
        "🔋 Batterie + données",
        "🔌 Estimation batterie",
        "🏢 Entreprise HT",
        "⚙️ Paramètres",
    ])

    with tab1:
        tab_installation_complete(s)
    with tab2:
        tab_batterie_donnees_completes(s)
    with tab3:
        tab_estimation_batterie(s)
    with tab4:
        tab_entreprise(s)
    with tab5:
        tab_parametres()


if __name__ == "__main__":
    main()
