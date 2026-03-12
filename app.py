import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
import math
import base64

st.set_page_config(
    page_title="OPR ArmyBuilder FR",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# CSS
# ======================================================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background: transparent;}
.stApp {background: #e9ecef; color: #212529;}
section[data-testid="stSidebar"] {background: #dee2e6; border-right: 1px solid #adb5bd; box-shadow: 2px 0 5px rgba(0,0,0,0.1);}
h1, h2, h3 {color: #202c45; letter-spacing: 0.04em; font-weight: 600;}
.stSelectbox, .stNumberInput, .stTextInput {background-color: white; border-radius: 6px; border: 1px solid #ced4da; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s ease;}
.stSelectbox:hover, .stNumberInput:hover, .stTextInput:hover {border-color: #3498db; box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);}
.stSelectbox > div, .stNumberInput > div, .stTextInput > div {border-radius: 6px !important;}
.stSelectbox label, .stNumberInput label, .stTextInput label {color: #2c3e50; font-weight: 500; margin-bottom: 0.3rem;}
button[kind="primary"] {background: linear-gradient(135deg, #2980b9, #1e5aa8) !important; color: white !important; font-weight: bold; border-radius: 6px; padding: 0.6rem 1rem; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s ease;}
button[kind="primary"]:hover {background: linear-gradient(135deg, #1e5aa8, #194b8d) !important; box-shadow: 0 4px 8px rgba(0,0,0,0.15); transform: translateY(-1px);}
.badge {display: inline-block; padding: 0.35rem 0.75rem; border-radius: 4px; background: #2980b9; color: white; font-size: 0.8rem; margin-bottom: 0.75rem; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.1);}
.card {background: #ffffff; border: 2px solid #2980b9; border-radius: 8px; padding: 1.2rem; transition: all 0.2s ease; cursor: pointer; box-shadow: 0 2px 8px rgba(41, 128, 185, 0.2);}
.card:hover {border-color: #1e5aa8; box-shadow: 0 4px 16px rgba(41, 128, 185, 0.3); transform: translateY(-2px);}
.stButton>button {background-color: #f8f9fa; border: 1px solid #ced4da; border-radius: 6px; padding: 0.5rem 1rem; color: #212529; font-weight: 500; transition: all 0.2s ease;}
.stButton>button:hover {background-color: #e9ecef; border-color: #3498db; color: #2980b9;}
.stColumn {padding: 0.5rem;}
.stDivider {margin: 1.5rem 0; border-top: 1px solid #adb5bd;}
.stAlert {border-radius: 6px; padding: 0.75rem 1.25rem;}
.stProgress > div > div > div {background-color: #2980b9 !important;}
.stSelectbox div[role="button"] {background-color: white !important; border: 1px solid #ced4da !important; border-radius: 6px !important;}
.stSelectbox div[role="button"]:focus, .stNumberInput input:focus, .stTextInput input:focus {border-color: #3498db !important; box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2) !important;}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR – CONTEXTE & NAVIGATION MODIFIÉE (version corrigée)
# ======================================================
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

# ======================================================
# INITIALISATION
# ======================================================
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
    st.session_state.points = 0
if "list_name" not in st.session_state:
    st.session_state.list_name = ""
if "units" not in st.session_state:
    st.session_state.units = []
if "faction_special_rules" not in st.session_state:
    st.session_state.faction_special_rules = []
if "faction_spells" not in st.session_state:
    st.session_state.faction_spells = {}

# ======================================================
# CONFIGURATION DES JEUX OPR (EXTENSIBLE)
# ======================================================
GAME_CONFIG = {
    "Age of Fantasy": {
        "min_points": 250, "max_points": 10000, "default_points": 1000,
        "hero_limit": 375, "unit_copy_rule": 750, "unit_max_cost_ratio": 0.35, "unit_per_points": 150
    },
    "Age of Fantasy: Regiments": {
        "min_points": 500, "max_points": 20000, "default_points": 2000,
        "hero_limit": 500, "unit_copy_rule": 1000, "unit_max_cost_ratio": 0.4, "unit_per_points": 200
    },
    "Grimdark Future": {
        "min_points": 250, "max_points": 10000, "default_points": 1000,
        "hero_limit": 375, "unit_copy_rule": 750, "unit_max_cost_ratio": 0.35, "unit_per_points": 150
    },
    "Grimdark Future: Firefight": {
        "min_points": 150, "max_points": 1000, "default_points": 300,
        "hero_limit": 300, "unit_copy_rule": 300, "unit_max_cost_ratio": 0.6, "unit_per_points": 100
    },
    "Age of Fantasy: Skirmish": {
        "min_points": 150, "max_points": 1000, "default_points": 300,
        "hero_limit": 300, "unit_copy_rule": 300, "unit_max_cost_ratio": 0.6, "unit_per_points": 100
    }
}

# ======================================================
# FONCTIONS DE VALIDATION
# ======================================================
def check_hero_limit(army_list, army_points, game_config):
    max_heroes = math.floor(army_points / game_config["hero_limit"])
    hero_count = sum(1 for unit in army_list if unit.get("type") == "hero")
    if hero_count > max_heroes:
        st.error(f"Limite de héros dépassée! Max: {max_heroes} (1 héros/{game_config['hero_limit']} pts)")
        return False
    return True

def check_unit_max_cost(army_list, army_points, game_config, new_unit_cost=None):
    max_cost = army_points * game_config["unit_max_cost_ratio"]
    for unit in army_list:
        if unit["cost"] > max_cost:
            st.error(f"Unité {unit['name']} dépasse {int(max_cost)} pts (35% du total)")
            return False
    if new_unit_cost and new_unit_cost > max_cost:
        st.error(f"Cette unité dépasse {int(max_cost)} pts (35% du total)")
        return False
    return True

def check_unit_copy_rule(army_list, army_points, game_config):
    x_value = math.floor(army_points / game_config["unit_copy_rule"])
    max_copies = 1 + x_value
    unit_counts = {}
    for unit in army_list:
        name = unit["name"]
        unit_counts[name] = unit_counts.get(name, 0) + 1
    for unit_name, count in unit_counts.items():
        if count > max_copies:
            st.error(f"Trop de copies de {unit_name}! Max: {max_copies}")
            return False
    return True

def validate_army_rules(army_list, army_points, game):
    game_config = GAME_CONFIG.get(game, {})
    return (check_hero_limit(army_list, army_points, game_config) and
            check_unit_max_cost(army_list, army_points, game_config) and
            check_unit_copy_rule(army_list, army_points, game_config))

def check_weapon_conditions(unit_key, requires):
    if not requires:
        return True

    current_weapons = []
    for selection in st.session_state.unit_selections.get(unit_key, {}).values():
        if isinstance(selection, dict) and "weapon" in selection:
            weapon = selection["weapon"]
            if isinstance(weapon, dict):
                current_weapons.append(weapon)
            elif isinstance(weapon, list):
                current_weapons.extend(weapon)
        elif isinstance(selection, str) and selection != "Aucune amélioration" and selection != "Aucune arme":
            weapon_name = selection.split(" (")[0]
            current_weapons.append({"name": weapon_name})

    for req in requires:
        if not any(w.get("name") == req or req in w.get("tags", []) for w in current_weapons):
            return False
    return True

# ======================================================
# FONCTIONS UTILITAIRES
# ======================================================
def format_unit_option(u):
    """Formate l'option d'unité avec plus de détails"""
    name_part = f"{u['name']}"
    if u.get('type') == "hero":
        name_part += " [1]"
    else:
        name_part += f" [{u.get('size', 10)}]"

    # Récupération des armes de base avec leur profil complet
    weapons = u.get('weapon', [])
    weapon_profiles = []
    if isinstance(weapons, list) and weapons:
        for weapon in weapons:
            if isinstance(weapon, dict):
                weapon_name = weapon.get('name', 'Arme')
                attacks = weapon.get('attacks', '?')
                ap = weapon.get('armor_piercing', '?')
                range_text = weapon.get('range', 'Mêlée')
                special_rules = weapon.get('special_rules', [])

                # Formatage du profil complet
                profile = f"{weapon_name} (A{attacks}/PA{ap}/{range_text}"
                if special_rules:
                    profile += f", {', '.join(special_rules)})"
                else:
                    profile += ")"

                weapon_profiles.append(profile)
    elif isinstance(weapons, dict):
        weapon_name = weapons.get('name', 'Arme')
        attacks = weapons.get('attacks', '?')
        ap = weapons.get('armor_piercing', '?')
        range_text = weapons.get('range', 'Mêlée')
        special_rules = weapons.get('special_rules', [])

        profile = f"{weapon_name} (A{attacks}/PA{ap}/{range_text}"
        if special_rules:
            profile += f", {', '.join(special_rules)})"
        else:
            profile += ")"

        weapon_profiles.append(profile)

    weapon_text = ", ".join(weapon_profiles) if weapon_profiles else "Aucune"

    # Récupération des règles spéciales
    special_rules = u.get('special_rules', [])
    rules_text = []
    if isinstance(special_rules, list):
        for rule in special_rules:
            if isinstance(rule, str):
                rules_text.append(rule)
            elif isinstance(rule, dict):
                rules_text.append(rule.get('name', ''))

    rules_text = ", ".join(rules_text) if rules_text else "Aucune"

    # Construction du texte final SANS le coût
    qua_def = f"Déf {u.get('defense', '?')}+"

    return f"{name_part} | {qua_def} | {weapon_text} | {rules_text}"

def format_weapon_option(weapon, cost=0):
    if not weapon or not isinstance(weapon, dict):
        return "Aucune arme"

    name = weapon.get('name', 'Arme')
    attacks = weapon.get('attacks', '?')
    ap = weapon.get('armor_piercing', '?')
    range_text = weapon.get('range', 'Mêlée')

    profile = f"{name} (A{attacks}/PA{ap}/{range_text})"
    if cost > 0:
        profile += f" (+{cost} pts)"

    return profile

def format_weapon(weapon):
    if not weapon:
        return "Aucune arme"

    range_text = weapon.get('range', '-')
    attacks = weapon.get('attacks', '-')
    ap = weapon.get('armor_piercing', '-')
    special_rules = weapon.get('special_rules', [])

    if isinstance(range_text, (int, float)):
        range_text = str(range_text) + '"'
    elif range_text == "-" or range_text is None or str(range_text).lower() == "mêlée":
        range_text = "Mêlée"

    result = f"<table><tr><th>RNG</th><th>ATK</th><th>AP</th><th>SPE</th></tr><tr>"
    result += f"<td>{range_text}</td><td>{attacks}</td><td>{ap}</td>"

    if special_rules:
        result += f"<td>{', '.join(special_rules)}</td>"
    else:
        result += "<td>-</td>"

    result += "</tr></table>"
    return result

def format_mount_option(mount):
    if not mount or not isinstance(mount, dict):
        return "Aucune monture"

    name = mount.get('name', 'Monture')
    cost = mount.get('cost', 0)
    mount_data = mount.get('mount', {})
    weapons = mount_data.get('weapon', [])
    special_rules = mount_data.get('special_rules', [])
    coriace = mount_data.get('coriace_bonus', 0)
    spells = mount_data.get('spells', [])

    stats = []
    weapon_profiles = []

    # ... (le reste du code pour les armes et règles spéciales)

    # Pour les sorts de monture (si applicable)
    if spells:
        for spell in spells:
            if isinstance(spell, dict):
                stats.append(f"{spell.get('name', '')}")  # Sans le coût ici
            elif isinstance(spell, str):
                stats.append(spell)

    label = f"{name}"
    if stats:
        label += f" ({', '.join(stats)})"
    label += f" (+{cost} pts)"

    return label

# ======================================================
# EXPORT HTML
# ======================================================
def export_html(army_list, army_name, army_limit):
    def esc(txt):
        if txt is None:
            return ""
        return str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def get_special_rules(unit):
        """Extraire toutes les règles spéciales de l'unité SAUF celles des armes"""
        rules = set()
        if "special_rules" in unit:
            for rule in unit["special_rules"]:
                if isinstance(rule, str):
                    rules.add(rule)
        if "options" in unit:
            for group_name, opts in unit["options"].items():
                if isinstance(opts, list):
                    for opt in opts:
                        if "special_rules" in opt:
                            for rule in opt["special_rules"]:
                                if isinstance(rule, str):
                                    rules.add(rule)
        if "mount" in unit and unit.get("mount"):
            mount_data = unit["mount"].get("mount", {})
            if "special_rules" in mount_data:
                for rule in mount_data["special_rules"]:
                    if isinstance(rule, str):
                        rules.add(rule)
        return sorted(rules, key=lambda x: x.lower().replace('é', 'e').replace('è', 'e'))

    def get_french_type(unit):
        """Retourne le type français basé sur unit_detail"""
        if unit.get('type') == 'hero':
            return 'Héros'
        unit_detail = unit.get('unit_detail', 'unit')
        type_mapping = {
            'hero': 'Héros',
            'named_hero': 'Héros nommé',
            'unit': 'Unité de base',
            'light_vehicle': 'Véhicule léger',
            'vehicle': 'Véhicule/Monstre',
            'titan': 'Titan'
        }
        return type_mapping.get(unit_detail, 'Unité')

    def format_weapon_html(weapon):
        """Formate une arme pour l'affichage HTML avec mentions spéciales"""
        if not weapon:
            return ""

        weapon_name = esc(weapon.get('name', 'Arme'))
        range_text = weapon.get('range', '-')
        attacks = weapon.get('attacks', '-')
        ap = weapon.get('armor_piercing', '-')
        special_rules = weapon.get('special_rules', [])

        if isinstance(range_text, (int, float)):
            range_text = f'{range_text}"'
        elif range_text == "-" or range_text is None or str(range_text).lower() == "mêlée":
            range_text = "Mêlée"

        rules_text = ", ".join(special_rules) if special_rules else "-"

        # Ajouter les mentions spéciales
        mention = ""
        if weapon.get("_conditional", False):
            mention = " (un seul exemplaire)"
        elif weapon.get("_upgraded", False):
            count = weapon.get("_count", 1)
            mention = f" ({count} exemplaires)"

        return f"{weapon_name}{mention} | {range_text} | A{attacks} | PA{ap} | {esc(rules_text)}"

    def format_role_html(role):
        """Formate un rôle pour l'affichage HTML"""
        if not role or not isinstance(role, dict):
            return ""

        role_name = esc(role.get('name', ''))
        special_rules = role.get('special_rules', [])

        # Formatage des armes du rôle si elles existent
        weapons_html = ""
        if "weapon" in role:
            role_weapons = role.get("weapon", [])
            if isinstance(role_weapons, list):
                weapons_html = "<div style='margin-top: 8px;'>"
                for weapon in role_weapons:
                    if isinstance(weapon, dict):
                        weapons_html += f"""
                        <div style='margin-bottom: 4px;'>
                            {format_weapon_html(weapon)}
                        </div>
                        """
                weapons_html += "</div>"
            elif isinstance(role_weapons, dict):
                weapons_html = "<div style='margin-top: 8px;'>"
                weapons_html += f"""
                <div style='margin-bottom: 4px;'>
                    {format_weapon_html(role_weapons)}
                </div>
                """
                weapons_html += "</div>"

        # Formatage des règles spéciales en rectangles gris
        rules_html = ""
        if special_rules:
            rules_html = "<div style='margin-top: 8px;'>"
            rules_html += "<div style='display: flex; flex-wrap: wrap; gap: 4px;'>"
            for rule in special_rules:
                rules_html += f"<span class='rule-tag'>{esc(rule)}</span>"
            rules_html += "</div>"
            rules_html += "</div>"

        return f"""
        <div style='margin-top: 10px; margin-bottom: 10px; padding: 8px; background: rgba(240, 248, 255, 0.3); border-radius: 6px; border-left: 3px solid #3498db;'>
            <div style='font-weight: 600; color: #3498db; margin-bottom: 5px;'>
                {role_name}
            </div>
            {weapons_html}
            {rules_html}
        </div>
        """

    # Trier la liste pour afficher les héros en premier
    sorted_army_list = sorted(army_list, key=lambda x: 0 if x.get("type") == "hero" else 1)

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Liste d'Armée OPR - {esc(army_name)}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-dark: #f8f9fa;
  --bg-card: #ffffff;
  --bg-header: #e9ecef;
  --accent: #3498db;
  --text-main: #212529;
  --text-muted: #6c757d;
  --border: #dee2e6;
  --cost-color: #ff6b6b;
  --tough-color: #e74c3c;
}}

body {{
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: 'Inter', sans-serif;
  margin: 0;
  padding: 20px;
  line-height: 1.5;
}}

.army {{
  max-width: 800px;
  margin: 0 auto;
}}

.army-title {{
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}}

.army-summary {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  padding: 16px;
  border-radius: 8px;
  margin: 20px 0;
  border: 1px solid var(--border);
}}

.unit-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.unit-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}}

.unit-name {{
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.unit-cost {{
  font-family: monospace;
  font-size: 18px;
  font-weight: bold;
  color: var(--cost-color);
}}

.unit-type {{
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}}

.unit-stats {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  background: var(--bg-header);
  padding: 12px;
  border-radius: 6px;
  text-align: center;
  font-size: 12px;
  margin: 12px 0;
}}

.stat-item {{
  padding: 5px;
  display: flex;
  flex-direction: column;
  align-items: center;
}}

.stat-label {{
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 5px;
}}

.stat-value {{
  font-weight: bold;
  font-size: 16px;
  color: var(--text-main);
}}

.tough-value {{
  color: var(--tough-color) !important;
  font-weight: bold;
  font-size: 18px;
}}

.section-title {{
  font-weight: 600;
  margin: 15px 0 8px 0;
  color: var(--text-main);
  font-size: 14px;
}}

.weapon-item {{
  background: var(--bg-header);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
}}

.weapon-name {{
  font-weight: 500;
  color: var(--text-main);
  flex: 1;
}}

.weapon-stats {{
  text-align: right;
  white-space: nowrap;
  flex: 1;
}}

.weapon-list {{
  margin: 10px 0;
  padding-left: 10px;
  border-left: 3px solid var(--accent);
}}

.weapon-entry {{
  margin-bottom: 5px;
  font-size: 14px;
}}

.rules-section {{
  margin: 12px 0;
}}

.rules-title {{
  font-weight: 600;
  margin-bottom: 6px;
  color: #3498db;
  font-size: 14px;
}}

.rules-list {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}}

.rule-tag {{
  background: var(--bg-header);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-main);
}}

.summary-cost {{
  font-family: monospace;
  font-size: 24px;
  font-weight: bold;
  color: var(--cost-color);
}}

.role-section {{
  background: rgba(240, 248, 255, 0.3);
  padding: 10px;
  border-radius: 6px;
  margin: 10px 0;
  border-left: 3px solid #3498db;
}}

.role-title {{
  font-weight: 600;
  color: #3498db;
  margin-bottom: 5px;
  font-size: 14px;
}}

.mount-section {{
  background: rgba(150, 150, 150, 0.1);
  border: 1px solid rgba(150, 150, 150, 0.3);
  padding: 10px;
  border-radius: 6px;
  margin: 15px 0;
}}

@media print {{
  body {{
    background: white;
    color: black;
  }}
  .unit-card, .army-summary {{
    background: white;
    border: 1px solid #ccc;
    page-break-inside: avoid;
  }}
}}
</style>
</head>
<body>
<div class="army">
  <!-- Titre de la liste -->
  <div class="army-title">
    {esc(army_name)} - {sum(unit['cost'] for unit in sorted_army_list)}/{army_limit} pts
  </div>

  <!-- Résumé de l'armée -->
  <div class="army-summary">
    <div style="font-size: 14px; color: var(--text-main);">
      <span style="color: var(--text-muted);">Nombre d'unités:</span>
      <strong style="margin-left: 8px; font-size: 18px;">{len(sorted_army_list)}</strong>
    </div>
    <div class="summary-cost">
      {sum(unit['cost'] for unit in sorted_army_list)}/{army_limit} pts
    </div>
  </div>
"""

    for unit in sorted_army_list:
        name = esc(unit.get("name", "Unité"))
        cost = unit.get("cost", 0)
        quality = esc(unit.get("quality", "-"))
        defense = esc(unit.get("defense", "-"))
        unit_type_french = get_french_type(unit)
        unit_size = unit.get("size", 10)
        coriace = unit.get("coriace", 0)

        if unit.get("type") == "hero":
            unit_size = 1

        # Récupération des armes avec vérification d'existence
        weapons = []
        if "weapon" in unit:
            weapons = unit.get("weapon", [])
            if not isinstance(weapons, list):
                weapons = [weapons] if weapons else []

        # Récupération des règles spéciales (sans celles des armes)
        special_rules = get_special_rules(unit)

        # Récupération des options et montures
        options = unit.get("options", {})
        mount = unit.get("mount", None)

        html += f'''
<div class="unit-card">
  <div class="unit-header">
    <div>
      <h3 class="unit-name">
        {name}
        <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">[{unit_size}]</span>
      </h3>
      <div class="unit-type">
        {"★" if unit.get("type") == "hero" else "🛡️"} {unit_type_french}
      </div>
    </div>
    <div class="unit-cost">{cost} pts</div>
  </div>

  <!-- Première ligne : Infos de base -->
  <div class="unit-stats">
    <div class="stat-item">
      <div class="stat-label">⚔️ Qualité</div>
      <div class="stat-value">{quality}+</div>
    </div>
    <div class="stat-item">
      <div class="stat-label">🛡️ Défense</div>
      <div class="stat-value">{defense}+</div>
    </div>
    <div class="stat-item">
      <div class="stat-label">❤️ Coriace</div>
      <div class="stat-value tough-value">{coriace if coriace > 0 else "-"}</div>
    </div>
    <div class="stat-item">
      <div class="stat-label">👥 Taille</div>
      <div class="stat-value">{unit_size}</div>
    </div>
  </div>
'''

        # Deuxième ligne : Armes (seulement si des armes existent)
        if weapons and len(weapons) > 0:
            html += '''
          <div class="weapon-list">
            <div style="font-weight: 600; margin-bottom: 5px; color: var(--accent);">Armes :</div>
        '''

            # Organiser les armes : d'abord les armes améliorées, puis les armes de base
            upgraded_weapons = []
            base_weapons = []

            for weapon in weapons:
                if weapon and isinstance(weapon, dict):
                    if weapon.get("_upgraded", False):
                        upgraded_weapons.append(weapon)
                    else:
                        base_weapons.append(weapon)

            # Afficher d'abord les armes améliorées
            for weapon in upgraded_weapons:
                html += f'''
            <div class="weapon-entry">
              {format_weapon_html(weapon)}
            </div>
        '''

            # Puis afficher les armes de base (si elles existent et n'ont pas toutes été remplacées)
            if base_weapons:
                for weapon in base_weapons:
                    # Vérifier si cette arme de base a été complètement remplacée
                    weapon_name = weapon.get('name', '')
                    is_replaced = False

                    for upgraded_weapon in upgraded_weapons:
                        if weapon_name in upgraded_weapon.get("_replaces", []):
                            # Vérifier si TOUTES les occurrences ont été remplacées
                            replace_count = upgraded_weapon.get("_count", 0)
                            unit_size = unit.get("size", 1)
                            if replace_count >= unit_size:
                                is_replaced = True
                                break

                    # N'afficher que si l'arme n'a pas été complètement remplacée
                    if not is_replaced:
                        html += f'''
            <div class="weapon-entry">
              {format_weapon_html(weapon)}
            </div>
        '''

            html += '''
          </div>
        '''

        # RÔLES ET AMÉLIORATIONS (pour les héros et titans uniquement)
        if options and unit.get("type") in ["hero", "titan"]:
            html += """
            <div style='margin-top: 15px;'>
                <div style='font-weight: 600; margin-bottom: 8px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 4px;'>
                    Améliorations:
                </div>
            """

            # Affichage des rôles
            for group_name, opts in options.items():
                if isinstance(opts, list) and opts:
                    for opt in opts:
                        if isinstance(opt, dict):
                            html += format_role_html(opt)

            html += """
            </div>
            """

        # Règles spéciales (hors armes et hors règles des rôles déjà affichées)
        if special_rules and len(special_rules) > 0:
            html += '''
  <div class="rules-section">
    <div class="rules-title">Règles spéciales:</div>
    <div class="rules-list">
'''
            for rule in special_rules:
                html += f'<span class="rule-tag">{esc(rule)}</span>'
            html += '''
    </div>
  </div>
'''

        # Monture (si elle existe)
        if mount:
            mount_data = mount.get("mount", {})
            mount_name = esc(mount.get("name", "Monture"))
            mount_weapons = mount_data.get("weapon", [])

            html += f'''
  <div class="mount-section">
    <div style="font-weight: 600; margin-bottom: 5px; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
      <span>🐴</span>
      <span>{mount_name}</span>
    </div>
'''

            if mount_weapons and len(mount_weapons) > 0:
                html += '''
    <div style="margin-top: 8px;">
      <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-main);">Armes de la monture:</div>
      <div class="weapon-list" style="margin-left: 15px;">
'''
                if isinstance(mount_weapons, list):
                    for weapon in mount_weapons:
                        if weapon:
                            html += f'''
        <div class="weapon-entry">
          {format_weapon_html(weapon)}
        </div>
'''
                html += '''
      </div>
    </div>
'''

            html += '''
  </div>
'''

        html += '</div>'

    # Légende des règles spéciales de la faction
    if sorted_army_list and hasattr(st.session_state, 'faction_special_rules') and st.session_state.faction_special_rules:
        faction_rules = st.session_state.faction_special_rules
        all_rules = [rule for rule in faction_rules if isinstance(rule, dict)]

        if all_rules and len(all_rules) > 0:
            html += '''
<div class="faction-rules">
  <h3 style="text-align: center; color: #3498db; border-top: 1px solid var(--border); padding-top: 10px; margin-bottom: 15px;">
    Légende des règles spéciales de la faction
  </h3>
  <div style="display: flex; flex-wrap: wrap;">
'''

            half = len(all_rules) // 2
            if len(all_rules) % 2 != 0:
                half += 1

            html += '<div style="flex: 1; min-width: 300px; padding-right: 15px;">'
            for rule in sorted(all_rules[:half], key=lambda x: x.get('name', '').lower().replace('é', 'e').replace('è', 'e')):
                if isinstance(rule, dict):
                    html += f'''
    <div style="margin-bottom: 10px;">
      <div style="color: #3498db; font-weight: bold;">{esc(rule.get('name', ''))}:</div>
      <div style="font-size: 14px; color: var(--text-main);">{esc(rule.get('description', ''))}</div>
    </div>
'''
            html += '</div>'

            html += '<div style="flex: 1; min-width: 300px; padding-left: 15px;">'
            for rule in sorted(all_rules[half:], key=lambda x: x.get('name', '').lower().replace('é', 'e').replace('è', 'e')):
                if isinstance(rule, dict):
                    html += f'''
    <div style="margin-bottom: 10px;">
      <div style="color: #3498db; font-weight: bold;">{esc(rule.get('name', ''))}:</div>
      <div style="font-size: 14px; color: var(--text-main);">{esc(rule.get('description', ''))}</div>
    </div>
'''
            html += '</div>'

            html += '''
  </div>
</div>
'''

    # Légende des sorts de la faction
    if sorted_army_list and hasattr(st.session_state, 'faction_spells') and st.session_state.faction_spells:
        spells = st.session_state.faction_spells
        all_spells = [{"name": name, "details": details} for name, details in spells.items() if isinstance(details, dict)]

        if all_spells and len(all_spells) > 0:
            html += '''
<div class="spells-section">
  <h3 style="text-align: center; color: #3498db; border-top: 1px solid var(--border); padding-top: 10px; margin-bottom: 15px;">
    Légende des sorts de la faction
  </h3>
  <div style="display: flex; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 100%;">
'''
            for spell in sorted(all_spells, key=lambda x: x['name'].lower().replace('é', 'e').replace('è', 'e')):
                if isinstance(spell, dict):
                    html += f'''
      <div style="margin-bottom: 12px; padding: 8px; background: rgba(240, 248, 255, 0.2); border-radius: 4px;">
        <div>
          <span style="color: #3498db; font-weight: bold; font-size: 16px;">{esc(spell.get('name', ''))}</span>
        </div>
        <div style="font-size: 14px; color: var(--text-main); margin-top: 4px;">
          {esc(spell.get('details', {}).get('description', ''))}
        </div>
      </div>
'''
            html += '''
    </div>
  </div>
</div>
'''

    html += '''
<div style="text-align: center; margin-top: 30px; font-size: 12px; color: var(--text-muted);">
  Généré par OPR ArmyBuilder FR - {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
</div>
</body>
</html>
'''
    return html
