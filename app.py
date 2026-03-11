import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import math
import base64
import os

# Initialisation des variables de session
if "page" not in st.session_state:
    st.session_state.page = "setup"
if "army_list" not in st.session_state:
    st.session_state.army_list = []
if "army_cost" not in st.session_state:
    st.session_state.army_cost = 0
if "unit_selections" not in st.session_state:
    st.session_state.unit_selections = {}
if "game" not in st.session_state:
    st.session_state.game = None
if "faction" not in st.session_state:
    st.session_state.faction = None
if "points" not in st.session_state:
    st.session_state.points = 1000
if "list_name" not in st.session_state:
    st.session_state.list_name = f"Liste_{datetime.now().strftime('%Y%m%d')}"
if "units" not in st.session_state:
    st.session_state.units = []
if "faction_special_rules" not in st.session_state:
    st.session_state.faction_special_rules = []
if "faction_spells" not in st.session_state:
    st.session_state.faction_spells = {}
if "unit_filter" not in st.session_state:
    st.session_state.unit_filter = "Tous"

# SIDEBAR – CONTEXTE & NAVIGATION
with st.sidebar:
    st.markdown("<div style='height:1px;'></div>", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛡️ OPR ArmyBuilder FR")

    st.subheader("📋 Armée")

    game = st.session_state.get("game", "—")
    faction = st.session_state.get("faction", "—")
    points = st.session_state.get("points", 0)
    army_cost = st.session_state.get("army_cost", 0)

    st.markdown(f"**Jeu :** {game}")
    st.markdown(f"**Faction :** {faction}")
    st.markdown(f"**Format :** {points} pts")

    if points > 0:
        st.progress(min(army_cost / points, 1.0))
        st.markdown(f"**Coût :** {army_cost} / {points} pts")

        if army_cost > points:
            st.error("⚠️ Dépassement de points")

        # NOUVELLES INFORMATIONS AJOUTÉES (version corrigée)
        if st.session_state.page == "army" and hasattr(st.session_state, 'army_list') and 'game' in st.session_state:
            # Utilisation des valeurs par défaut de GAME_CONFIG
            units_cap = math.floor(points / 150)  # Valeur par défaut de unit_per_points
            heroes_cap = math.floor(points / 375)  # Valeur par défaut de hero_limit

            units_now = len([u for u in st.session_state.army_list if u.get("type") != "hero"])
            heroes_now = len([u for u in st.session_state.army_list if u.get("type") == "hero"])

            st.markdown(f"**Unités :** {units_now} / {units_cap}")
            st.markdown(f"**Héros :** {heroes_now} / {heroes_cap}")

    st.divider()

# Configuration de la page
st.set_page_config(
    page_title="OPR ArmyBuilder FR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background: transparent;}

.stApp {
    background: #e9ecef;
    color: #212529;
}

section[data-testid="stSidebar"] {
    background: #dee2e6;
    border-right: 1px solid #adb5bd;
}

h1, h2, h3 {
    color: #202c45;
    letter-spacing: 0.04em;
    font-weight: 600;
}

.stSelectbox, .stNumberInput, .stTextInput {
    background-color: white;
    border-radius: 6px;
    border: 1px solid #ced4da;
}

.filter-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 20px 0;
}

.filter-button {
    padding: 8px 15px;
    border-radius: 6px;
    border: 1px solid #ddd;
    background-color: #f8f9fa;
    color: #495057;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
}

.weapon-item {
    background: #f0f8ff;
    padding: 8px;
    border-radius: 4px;
    margin: 5px 0;
    border-left: 3px solid #3498db;
}
</style>
""", unsafe_allow_html=True)

# Configuration des jeux
GAME_CONFIG = {
    "Age of Fantasy": {
        "min_points": 250,
        "max_points": 10000,
        "default_points": 1000,
        "hero_limit": 375,
        "unit_copy_rule": 750,
        "unit_max_cost_ratio": 0.35,
        "unit_per_points": 150
    }
}

def format_weapon_option(weapon, cost=0):
    """Formate l'option d'arme pour la sélection"""
    if not weapon or not isinstance(weapon, dict):
        return "Aucune arme"

    name = weapon.get('name', 'Arme')
    attacks = weapon.get('attacks', '?')
    ap = weapon.get('armor_piercing', '?')
    range_text = weapon.get('range', 'Mêlée')
    special_rules = weapon.get('special_rules', [])

    profile = f"{name} ({range_text}, A{attacks}"
    if ap not in ("-", 0, "0", None):
        profile += f"/PA{ap}"
    profile += ")"

    if special_rules:
        profile += f" | {', '.join(special_rules)}"

    if cost > 0:
        profile += f" (+{cost} pts)"

    return profile

@st.cache_data
def load_factions():
    """Charge les factions depuis les fichiers JSON"""
    factions = {}
    games = set()

    try:
        # Chemin vers le dossier des factions
        FACTIONS_DIR = Path(__file__).resolve().parent / "frontend" / "public" / "factions"
        if not FACTIONS_DIR.exists():
            FACTIONS_DIR = Path(__file__).resolve().parent / "lists" / "data" / "factions"

        # Charger chaque fichier JSON
        for fp in FACTIONS_DIR.glob("*.json"):
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                    game = data.get("game")
                    faction = data.get("faction")
                    if game and faction:
                        if game not in factions:
                            factions[game] = {}
                        factions[game][faction] = data
                        games.add(game)
            except Exception as e:
                st.warning(f"Erreur chargement {fp.name}: {e}")
    except Exception as e:
        st.error(f"Erreur chargement factions: {e}")
        return {}, []

    return factions, sorted(games) if games else []

# Page de configuration
if st.session_state.page == "setup":
    st.title("🛡️ OPR ArmyBuilder FR")

    factions_by_game, games = load_factions()
    if not games:
        st.error("Aucun jeu trouvé")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.session_state.game = st.selectbox(
            "Jeu",
            games,
            index=0 if st.session_state.game not in games else games.index(st.session_state.game)
        )

    with col2:
        faction_options = list(factions_by_game.get(st.session_state.game, {}).keys())
        if not faction_options:
            st.error("Aucune faction disponible")
            st.stop()

        st.session_state.faction = st.selectbox(
            "Faction",
            faction_options,
            index=0
        )

    with col3:
        game_cfg = GAME_CONFIG.get(st.session_state.game, {})
        st.session_state.points = st.number_input(
            "Points",
            min_value=game_cfg.get("min_points", 250),
            max_value=game_cfg.get("max_points", 10000),
            value=game_cfg.get("default_points", 1000)
        )

    st.session_state.list_name = st.text_input(
        "Nom de la liste",
        value=st.session_state.list_name
    )

    if st.button("Créer l'armée"):
        faction_data = factions_by_game[st.session_state.game][st.session_state.faction]
        st.session_state.units = faction_data.get("units", [])
        st.session_state.faction_special_rules = faction_data.get("faction_special_rules", [])
        st.session_state.faction_spells = faction_data.get("spells", {})

        st.session_state.army_list = []
        st.session_state.army_cost = 0
        st.session_state.unit_selections = {}

        st.session_state.page = "army"
        st.rerun()

# Page de construction d'armée
if st.session_state.page == "army":
    # Vérifications initiales
    if not all(key in st.session_state for key in ["game", "faction", "points", "units"]):
        st.error("Configuration incomplète")
        if st.button("Retour à la configuration"):
            st.session_state.page = "setup"
            st.rerun()
        st.stop()

    st.title(f"{st.session_state.list_name} - {st.session_state.army_cost}/{st.session_state.points} pts")

    # Section Export/Import
    colE1, colE2, colE3 = st.columns(3)
    with colE1:
        if st.button("Export JSON"):
            json_data = json.dumps({
                "game": st.session_state.game,
                "faction": st.session_state.faction,
                "points": st.session_state.points,
                "list_name": st.session_state.list_name,
                "army_list": st.session_state.army_list,
                "army_cost": st.session_state.army_cost
            }, indent=2, ensure_ascii=False)
            st.download_button(
                "Télécharger JSON",
                data=json_data,
                file_name=f"{st.session_state.list_name}.json",
                mime="application/json"
            )

    # Filtres et sélection d'unité
    st.subheader("Filtres")
    filter_categories = {
        "Tous": None,
        "Héros": ["hero"],
        "Unités": ["unit"]
    }

    for category in filter_categories:
        if st.button(category):
            st.session_state.unit_filter = category
            st.rerun()

    filtered_units = st.session_state.units
    if st.session_state.unit_filter != "Tous":
        filtered_units = [
            u for u in st.session_state.units
            if u.get('unit_detail') in filter_categories[st.session_state.unit_filter]
        ]

    if not filtered_units:
        st.warning("Aucune unité disponible avec ce filtre")
        st.stop()

    unit = st.selectbox(
        "Sélectionnez une unité",
        filtered_units,
        format_func=lambda u: f"{u['name']} ({u.get('base_cost', 0)} pts)"
    )

    # Configuration de l'unité
    unit_key = f"unit_{unit['name']}"
    if unit_key not in st.session_state.unit_selections:
        st.session_state.unit_selections[unit_key] = {}

    weapons = unit.get("weapon", [])
    if not isinstance(weapons, list):
        weapons = [weapons]

    selected_options = {}
    weapon_cost = 0
    upgrades_cost = 0
    weapon_upgrades = []

    # Gestion des groupes d'améliorations
    for g_idx, group in enumerate(unit.get("upgrade_groups", [])):
        g_key = f"group_{g_idx}"
        st.subheader(group.get("group", "Améliorations"))

        # AMÉLIORATIONS PAR FIGURINE (variable_weapon_count)
        if group.get("type") == "variable_weapon_count":
            opt = group.get("options", [{}])[0]
            if not opt:
                continue

            # Compter les armes remplaçables
            replaceable_weapons = [w for w in weapons if w.get("name") in opt.get("replaces", [])]
            max_count = min(
                calculate_max_count(unit, opt.get("max_count", {"type": "fixed", "value": 1})),
                len(replaceable_weapons)
            )

            count = st.slider(
                f"Nombre de {opt.get('name', 'améliorations')} (0-{max_count})",
                min_value=0,
                max_value=max_count,
                value=0,
                key=f"{unit_key}_{g_key}_count"
            )

            if count > 0:
                total_cost = count * opt.get("cost_per_unit", opt.get("cost", 0))
                upgrades_cost += total_cost

                # Stocker la sélection
                st.session_state.unit_selections[unit_key][g_key] = {
                    "count": count,
                    "total_cost": total_cost,
                    "weapon": opt.get("weapon")
                }

                # Remplacer les armes
                for i in range(count):
                    if replaceable_weapons:
                        index = weapons.index(replaceable_weapons[0])
                        weapons[index] = opt["weapon"].copy()
                        replaceable_weapons.pop(0)

        # AUTRES TYPES D'AMÉLIORATIONS
        elif group.get("type") == "upgrades":
            for opt in group.get("options", []):
                opt_key = f"{g_key}_{opt['name']}"
                if st.checkbox(f"{opt['name']} (+{opt['cost']} pts)", key=opt_key):
                    upgrades_cost += opt["cost"]
                    if "special_rules" in opt:
                        selected_options[opt["name"]] = opt

    # Calcul du coût final
    multiplier = 1
    if unit.get("type") != "hero" and st.checkbox("Unité combinée"):
        multiplier = 2

    final_cost = (unit.get("base_cost", 0) + upgrades_cost) * multiplier

    if st.button(f"Ajouter à l'armée ({final_cost} pts)"):
        unit_data = {
            "name": unit["name"],
            "type": unit.get("type", "unit"),
            "cost": final_cost,
            "size": unit.get("size", 10) * multiplier if unit.get("type") != "hero" else 1,
            "quality": unit.get("quality", 3),
            "defense": unit.get("defense", 3),
            "weapon": weapons,
            "options": selected_options
        }

        st.session_state.army_list.append(unit_data)
        st.session_state.army_cost += final_cost
        st.rerun()

    # Affichage de la liste d'armée
    st.subheader("Liste d'armée actuelle")
    for i, unit_data in enumerate(st.session_state.army_list):
        with st.expander(f"{unit_data['name']} - {unit_data['cost']} pts"):
            st.markdown(f"**Type:** {unit_data['type']}")
            st.markdown(f"**Taille:** {unit_data.get('size', '?')}")
            st.markdown(f"**Qualité:** {unit_data.get('quality', '?')}+")
            st.markdown(f"**Défense:** {unit_data.get('defense', '?')}+")

            st.markdown("**Armes:**")
            for weapon in unit_data.get("weapon", []):
                if isinstance(weapon, dict):
                    st.markdown(f"- {weapon.get('name', 'Arme')} (A{weapon.get('attacks', '?')}/PA{weapon.get('armor_piercing', '?')})")

            if st.button(f"Supprimer {unit_data['name']}", key=f"delete_{i}"):
                st.session_state.army_cost -= unit_data['cost']
                st.session_state.army_list.pop(i)
                st.rerun()
