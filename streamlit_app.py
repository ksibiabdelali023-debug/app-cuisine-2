import streamlit as st
import re
import statistics
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import requests

# CONSTANTES
NB_VARIANTES = 85
PHOTOS_PERSO, CODES_BARRES = {}, {}
EMOJIS = {"Salade Caprese": "🍅", "Avocat au Thon": "🥑", "Velouté de Potimarron": "🎃", "Crevettes Mayo": "🍤", "Poulet au Curry et Riz": "🍛", "Pavé de Saumon Aneth": "🐟", "Spaghetti Bolognaise": "🍝", "Gratin Dauphinois": "🥔", "Fondant au Chocolat": "🍫", "Tarte aux Pommes": "🥧", "Mousse au Chocolat": "🍮", "Tiramisu Café": "☕"}
DEGRADES = {"Entrée": "linear-gradient(135deg,#34D399,#A7F3D0)", "Plat": "linear-gradient(135deg,#FB923C,#FDBA74)", "Dessert": "linear-gradient(135deg,#F472B6,#FBCFE8)"}
CATEGORIES = {"Toutes": None, "Entrées": "Entrée", "Plats": "Plat", "Desserts": "Dessert"}
ARTICLES_WIKI = {"Salade Caprese": ("en", "Caprese salad"), "Avocat au Thon": ("en", "Avocado"), "Velouté de Potimarron": ("en", "Pumpkin soup"), "Crevettes Mayo": ("en", "Prawn cocktail"), "Poulet au Curry et Riz": ("en", "Chicken curry"), "Pavé de Saumon Aneth": ("en", "Salmon as food"), "Spaghetti Bolognaise": ("en", "Bolognese sauce"), "Gratin Dauphinois": ("fr", "Gratin dauphinois"), "Fondant au Chocolat": ("en", "Molten chocolate cake"), "Tarte aux Pommes": ("en", "Apple pie"), "Mousse au Chocolat": ("en", "Chocolate mousse"), "Tiramisu Café": ("en", "Tiramisu")}
BASE = [("Salade Caprese", "Entrée", "10 min", "Facile"), ("Avocat au Thon", "Entrée", "10 min", "Facile"), ("Velouté de Potimarron", "Entrée", "30 min", "Facile"), ("Crevettes Mayo", "Entrée", "15 min", "Facile"), ("Poulet au Curry et Riz", "Plat", "35 min", "Moyen"), ("Pavé de Saumon Aneth", "Plat", "20 min", "Facile"), ("Spaghetti Bolognaise", "Plat", "40 min", "Facile"), ("Gratin Dauphinois", "Plat", "1 h 15", "Moyen"), ("Fondant au Chocolat", "Dessert", "25 min", "Moyen"), ("Tarte aux Pommes", "Dessert", "50 min", "Moyen"), ("Mousse au Chocolat", "Dessert", "20 min", "Facile"), ("Tiramisu Café", "Dessert", "30 min", "Moyen")]
RAYONS_ORDRE = ["Fruits et légumes", "Viandes et poissons", "Crèmerie et œufs", "Épicerie"]
REGLES_RAYONS = [("Épicerie", ("concassées", "compote", "bouillon", "pâte brisée", "thon", "riz", "spaghetti", "huile", "curry", "farine", "sucre", "chocolat", "mayonnaise", "moutarde", "boudoirs", "café", "cacao")), ("Viandes et poissons", ("poulet", "bœuf", "saumon", "crevettes")), ("Crèmerie et œufs", ("mozzarella", "crème", "beurre", "lait", "emmental", "mascarpone", "œufs")), ("Fruits et légumes", ("tomates", "avocats", "potimarron", "oignon", "citron", "carotte", "pommes", "ail", "basilic", "aneth", "ciboulette", "salade"))]

FICHES = {
    "Salade Caprese": {"ingredients": [(3, "", "tomates mûres", 1.20, 1.40), (125, "g", "mozzarella à présure végétale", 1.50, 1.30), (1, "pot", "basilic frais", 1.10, 0.99), (2, "c. à soupe", "huile d'olive", 0.35, 0.30)], "etapes": ["Lavez les tomates", "Coupez la mozzarella", "Alternez les tranches", "Ajoutez l'huile"], "astuce": "Sortez les tomates avant.", "halal": "Présure végétale."},
    "Avocat au Thon": {"ingredients": [(2, "", "avocats mûrs", 1.80, 1.95), (1, "boîte", "thon au naturel (160 g)", 2.10, 1.90)], "etapes": ["Mélangez le thon", "Garnissez"], "astuce": "Citronnez.", "halal": "Vérifiez."},
    "Velouté de Potimarron": {"ingredients": [(600, "g", "potimarron", 2.50, 2.20), (1, "", "oignon", 0.25, 0.20)], "etapes": ["Cuire", "Mixer"], "astuce": "Muscade.", "halal": "Végétal."},
    "Crevettes Mayo": {"ingredients": [(250, "g", "crevettes décortiquées cuites", 4.50, 4.20)], "etapes": ["Mélanger"], "astuce": "Paprika.", "halal": "Admis."},
    "Poulet au Curry et Riz": {"ingredients": [(300, "g", "blanc de poulet halal", 6.50, 5.90), (150, "g", "riz basmati", 1.40, 1.20)], "etapes": ["Dorer", "Mijoter"], "astuce": "Rincer.", "halal": "Certifié."},
    "Pavé de Saumon Aneth": {"ingredients": [(2, "", "pavés de saumon", 8.90, 8.40)], "etapes": ["Enfourner"], "astuce": "Nacré.", "halal": "Aucune."},
    "Spaghetti Bolognaise": {"ingredients": [(200, "g", "spaghetti", 0.80, 0.75), (250, "g", "bœuf haché halal", 5.20, 5.50)], "etapes": ["Mijoter sauce", "Cuire pâtes"], "astuce": "Eau de cuisson.", "halal": "Certifié."},
    "Gratin Dauphinois": {"ingredients": [(800, "g", "pommes de terre", 2.10, 1.90)], "etapes": ["Couper", "Enfourner"], "astuce": "Ne pas rincer.", "halal": "Végétal."},
    "Fondant au Chocolat": {"ingredients": [(200, "g", "chocolat noir", 1.40, 1.20)], "etapes": ["Fondre", "Cuire 20 min"], "astuce": "Cœur coulant.", "halal": "Sans alcool."},
    "Tarte aux Pommes": {"ingredients": [(1, "", "pâte brisée pur beurre", 1.10, 0.95)], "etapes": ["Étaler", "Cuire"], "astuce": "Confiture.", "halal": "Pur beurre."},
    "Mousse au Chocolat": {"ingredients": [(150, "g", "chocolat pâtissier", 1.40, 1.20), (4, "", "œufs", 2.10, 2.30)], "etapes": ["Blancs en neige", "Mélanger"], "astuce": "Délicatement.", "halal": "Sans gélatine."},
    "Tiramisu Café": {"ingredients": [(250, "g", "mascarpone à présure végétale", 2.80, 2.50)], "etapes": ["Monter", "Réfrigérer"], "astuce": "La veille.", "halal": "Sans alcool."}
}

# FONCTIONS LOGIQUES
def format_prix(x): return f"{x:.2f}".replace(".", ",") + " €"
def format_qte(q): return f"{q:g}".replace(".", ",")
def ligne_ingredient(q, unite, nom): return f"{format_qte(q)} {unite} de {nom}" if unite else f"{nom.capitalize()} × {format_qte(q)}"
def minutes(t): return int(re.findall(r"\d+", t)[0]) if re.findall(r"\d+", t) else 0
def cout(ing, mag, coef=1.0): return sum(i[3 if mag == "leclerc" else 4] for i in ing) * coef
def prix_minimum(r): return min(cout(r["ingredients"], "leclerc"), cout(r["ingredients"], "lidl"))
def rayon_de(nom): return next((r for r, mots in REGLES_RAYONS if any(m in nom.lower() for m in mots)), "Épicerie")
def totaux(recettes, coef_de): return sum(cout(r["ingredients"], "leclerc", coef_de(r["id"])) for r in recettes), sum(cout(r["ingredients"], "lidl", coef_de(r["id"])) for r in recettes)

def agreger(recettes, coef_de):
    agg = {}
    for r in recettes:
        c = coef_de(r["id"])
        for q, u, n, pl, pd in r["ingredients"]:
            a = agg.setdefault((n, u), [0.0, 0.0, 0.0])
            a[0] += q * c
            a[1] += pl * c
            a[2] += pd * c
    return agg

def grouper_par_rayon(agg):
    g = {r: [] for r in RAYONS_ORDRE}
    for (n, u), (q, pl, pd) in sorted(agg.items()): g[rayon_de(n)].append((n, u, q, pl, pd))
    return [(r, l) for r, l in g.items() if l]

# APPLICATION APP
st.session_state.setdefault("selection", [])
st.session_state.setdefault("portions", {})

def coef_fn(rid): return st.session_state.portions.get(rid, 2) / 2

# Generation rapide
recettes = []
rid = 1
for i in range(2):
    for nom, cat, temps, diff in BASE:
        suf = "" if i == 0 else f" (variante {i+1})"
        recettes.append({"id": rid, "nom": nom + suf, "base": nom, "categorie": cat, "image": "", "temps": temps, "difficulte": diff, "ingredients": FICHES[nom]["ingredients"]})
        rid += 1
par_id = {r["id"]: r for r in recettes}

st.title("MiamMiam 🍳")
st.subheader("Recettes 100% Halal - Comparateur Leclerc vs Lidl")

sel = [par_id[i] for i in st.session_state.selection]
st.metric("Recettes au panier", len(sel))

o1, o2 = st.tabs(["Recettes", "Mon Panier"])

with o1:
    recherche = st.text_input("Rechercher un plat")
    for r in recettes:
        if recherche.lower() in r["nom"].lower():
            with st.container(border=True):
                st.write(f"### {r['nom']} ({r['categorie']})")
                st.write(f"Temps : {r['temps']} | Difficulté : {r['difficulte']}")
                
                # Système d'ajout/retrait
                if r["id"] in st.session_state.selection:
                    if st.button("Retirer", key=f"ret_{r['id']}"):
                        st.session_state.selection.remove(r["id"])
                        st.rerun()
                else:
                    if st.button("Ajouter au panier", key=f"add_{r['id']}", type="primary"):
                        st.session_state.selection.append(r["id"])
                        st.rerun()

with o2:
    if not sel:
        st.info("Votre panier est vide.")
    else:
        tl, td = totaux(sel, coef_fn)
        st.subheader("Comparatif total")
        st.write(f"**Total Leclerc :** {format_prix(tl)}")
        st.write(f"**Total Lidl :** {format_prix(td)}")
        
        st.divider()
        agg = agreger(sel, coef_fn)
        gr = grouper_par_rayon(agg)
        st.subheader("Liste de courses de vos articles")
        for rayon, lignes in gr:
            st.write(f"**{rayon}**")
            for n, u, q, pl, pd in lignes:
                st.checkbox(f"{ligne_ingredient(q, u, n)}")
