import streamlit as st
import re
import statistics
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import requests

# ==========================================
# 1. CONFIGURATION ET CONSTANTES (donnees)
# ==========================================
NB_VARIANTES = 85
PHOTOS_PERSO = {}
CODES_BARRES = {}

EMOJIS = {
    "Salade Caprese": "🍅", "Avocat au Thon": "🥑", "Velouté de Potimarron": "🎃",
    "Crevettes Mayo": "🍤", "Poulet au Curry et Riz": "🍛", "Pavé de Saumon Aneth": "🐟",
    "Spaghetti Bolognaise": "🍝", "Gratin Dauphinois": "🥔", "Fondant au Chocolat": "🍫",
    "Tarte aux Pommes": "🥧", "Mousse au Chocolat": "🍮", "Tiramisu Café": "☕",
}

DEGRADES = {
    "Entrée": "linear-gradient(135deg,#34D399,#A7F3D0)",
    "Plat": "linear-gradient(135deg,#FB923C,#FDBA74)",
    "Dessert": "linear-gradient(135deg,#F472B6,#FBCFE8)",
}

CAT = {"Entrée": "entree", "Plat": "plat", "Dessert": "dessert"}
CATEGORIES = {"Toutes": None, "Entrées": "Entrée", "Plats": "Plat", "Desserts": "Dessert"}

ARTICLES_WIKI = {
    "Salade Caprese": ("en", "Caprese salad"),
    "Avocat au Thon": ("en", "Avocado"),
    "Velouté de Potimarron": ("en", "Pumpkin soup"),
    "Crevettes Mayo": ("en", "Prawn cocktail"),
    "Poulet au Curry et Riz": ("en", "Chicken curry"),
    "Pavé de Saumon Aneth": ("en", "Salmon as food"),
    "Spaghetti Bolognaise": ("en", "Bolognese sauce"),
    "Gratin Dauphinois": ("fr", "Gratin dauphinois"),
    "Fondant au Chocolat": ("en", "Molten chocolate cake"),
    "Tarte aux Pommes": ("en", "Apple pie"),
    "Mousse au Chocolat": ("en", "Chocolate mousse"),
    "Tiramisu Café": ("en", "Tiramisu"),
}

BASE = [
    ("Salade Caprese", "Entrée", "10 min", "Facile"),
    ("Avocat au Thon", "Entrée", "10 min", "Facile"),
    ("Velouté de Potimarron", "Entrée", "30 min", "Facile"),
    ("Crevettes Mayo", "Entrée", "15 min", "Facile"),
    ("Poulet au Curry et Riz", "Plat", "35 min", "Moyen"),
    ("Pavé de Saumon Aneth", "Plat", "20 min", "Facile"),
    ("Spaghetti Bolognaise", "Plat", "40 min", "Facile"),
    ("Gratin Dauphinois", "Plat", "1 h 15", "Moyen"),
    ("Fondant au Chocolat", "Dessert", "25 min", "Moyen"),
    ("Tarte aux Pommes", "Dessert", "50 min", "Moyen"),
    ("Mousse au Chocolat", "Dessert", "20 min", "Facile"),
    ("Tiramisu Café", "Dessert", "30 min", "Moyen"),
]

RAYONS_ORDRE = ["Fruits et légumes", "Viandes et poissons", "Crèmerie et œufs", "Épicerie"]
REGLES_RAYONS = [
    ("Épicerie", ("concassées", "compote", "bouillon", "pâte brisée", "thon", "riz", "spaghetti", "huile",
                  "curry", "farine", "sucre", "chocolat", "mayonnaise", "moutarde", "boudoirs", "café", "cacao")),
    ("Viandes et poissons", ("poulet", "bœuf", "saumon", "crevettes")),
    ("Crèmerie et œufs", ("mozzarella", "crème", "beurre", "lait", "emmental", "mascarpone", "œufs")),
    ("Fruits et légumes", ("tomates", "avocats", "potimarron", "oignon", "citron", "carotte", "pommes",
                           "ail", "basilic", "aneth", "ciboulette", "salade")),
]

FICHES = {
    "Salade Caprese": {
        "ingredients": [
            (3, "", "tomates mûres", 1.20, 1.40),
            (125, "g", "mozzarella à présure végétale", 1.50, 1.30),
            (1, "pot", "basilic frais", 1.10, 0.99),
            (2, "c. à soupe", "huile d'olive", 0.35, 0.30)],
        "etapes": ["Lavez les tomates et coupez-les en rondelles de 5 mm.",
                   "Égouttez la mozzarella et coupez-la en tranches de même épaisseur.",
                   "Alternez tomates et mozzarella en les faisant se chevaucher sur une assiette.",
                   "Glissez les feuilles de basilic entre les tranches.",
                   "Arrosez d'huile d'olive, salez, poivrez et servez frais."],
        "astuce": "Sortez les tomates du frigo 30 minutes avant : elles auront bien plus de goût.",
        "halal": "Choisissez une mozzarella à présure végétale (ou certifiée halal)."},
    "Avocat au Thon": {
        "ingredients": [
            (2, "", "avocats mûrs", 1.80, 1.95),
            (1, "boîte", "thon au naturel (160 g)", 2.10, 1.90),
            (2, "c. à soupe", "mayonnaise", 0.30, 0.35),
            (1, "", "citron", 0.60, 0.50),
            (1, "pot", "ciboulette", 0.90, 0.85)],
        "etapes": ["Coupez les avocats en deux et retirez le noyau.",
                   "Égouttez le thon et émiettez-le dans un bol.",
                   "Mélangez le thon avec la mayonnaise, un filet de jus de citron et la ciboulette.",
                   "Garnissez les moitiés d'avocat avec la préparation.",
                   "Servez bien frais avec un trait de citron."],
        "astuce": "Arrosez la chair d'avocat de citron pour éviter qu'elle noircisse.",
        "halal": "Lisez l'étiquette de la mayonnaise : sans alcool ni additif d'origine animale douteuse."},
    "Velouté de Potimarron": {
        "ingredients": [
            (600, "g", "potimarron", 2.50, 2.20),
            (1, "", "oignon", 0.25, 0.20),
            (500, "ml", "bouillon de légumes", 0.40, 0.35),
            (10, "cl", "crème fraîche", 1.10, 1.25),
            (1, "noix", "beurre", 0.15, 0.14)],
        "etapes": ["Lavez le potimarron (la peau se mange), retirez les graines et coupez-le en cubes.",
                   "Faites revenir l'oignon émincé dans le beurre 3 minutes.",
                   "Ajoutez le potimarron et le bouillon chaud, puis cuisez 20 minutes à frémissement.",
                   "Mixez finement en ajoutant la crème fraîche.",
                   "Rectifiez l'assaisonnement et servez chaud."],
        "astuce": "Une pincée de noix de muscade et quelques graines de courge torréfiées pour la finition.",
        "halal": "Vérifiez que le bouillon est 100 % végétal (sans arôme d'origine porcine)."},
    "Crevettes Mayo": {
        "ingredients": [
            (250, "g", "crevettes décortiquées cuites", 4.50, 4.20),
            (3, "c. à soupe", "mayonnaise", 1.30, 1.45),
            (1, "c. à café", "moutarde", 0.15, 0.12),
            (1, "", "citron", 0.60, 0.50),
            (1, "", "salade (cœur de laitue)", 0.90, 0.80)],
        "etapes": ["Décongelez les crevettes si besoin et épongez-les avec du papier absorbant.",
                   "Mélangez mayonnaise, moutarde et un peu de jus de citron.",
                   "Ajoutez les crevettes et enrobez-les délicatement.",
                   "Dressez sur un lit de salade et servez bien frais."],
        "astuce": "Ajoutez une pointe de paprika ou de piment d'Espelette dans la sauce.",
        "halal": "Les crevettes sont admises par la plupart des écoles juridiques : référez-vous à la vôtre."},
    "Poulet au Curry et Riz": {
        "ingredients": [
            (300, "g", "blanc de poulet halal", 6.50, 5.90),
            (150, "g", "riz basmati", 1.40, 1.20),
            (1, "", "oignon", 0.25, 0.20),
            (2, "c. à café", "curry en poudre", 0.60, 0.55),
            (20, "cl", "crème liquide", 1.20, 1.10),
            (1, "c. à soupe", "huile", 0.15, 0.12)],
        "etapes": ["Coupez le poulet en dés et l'oignon en lamelles.",
                   "Faites dorer le poulet dans l'huile 5 minutes, réservez.",
                   "Faites revenir l'oignon, ajoutez le curry et mélangez 1 minute.",
                   "Remettez le poulet, versez la crème et laissez mijoter 15 minutes.",
                   "Pendant ce temps, cuisez le riz 10 à 12 minutes dans l'eau bouillante salée.",
                   "Servez le poulet sur le riz égoutté."],
        "astuce": "Rincez le riz basmati avant cuisson pour des grains bien séparés.",
        "halal": "Poulet certifié halal (abattage rituel) : rayon halal ou boucherie halal."},
    "Pavé de Saumon Aneth": {
        "ingredients": [
            (2, "", "pavés de saumon", 8.90, 8.40),
            (1, "bouquet", "aneth", 1.20, 0.99),
            (1, "", "citron", 0.60, 0.50),
            (1, "c. à soupe", "huile d'olive", 0.20, 0.18)],
        "etapes": ["Préchauffez le four à 180 °C.",
                   "Posez les pavés sur une feuille de papier cuisson, huilez, salez et poivrez.",
                   "Recouvrez d'aneth ciselé et de rondelles de citron.",
                   "Fermez la papillote et enfournez 12 à 15 minutes.",
                   "Servez avec du riz ou des légumes vapeur."],
        "astuce": "Le saumon est cuit quand il se détache en pétales mais reste nacré au centre.",
        "halal": "Poisson : aucune contrainte particulière."},
    "Spaghetti Bolognaise": {
        "ingredients": [
            (200, "g", "spaghetti", 0.80, 0.75),
            (250, "g", "bœuf haché halal", 5.20, 5.50),
            (1, "", "oignon", 0.25, 0.20),
            (1, "", "carotte", 0.20, 0.18),
            (400, "g", "tomates concassées", 0.95, 0.85),
            (1, "gousse", "ail", 0.15, 0.15)],
        "etapes": ["Hachez finement l'oignon, la carotte et l'ail.",
                   "Faites-les revenir 5 minutes dans un filet d'huile.",
                   "Ajoutez la viande et faites-la dorer en l'émiettant.",
                   "Versez les tomates, salez, poivrez et laissez mijoter 25 minutes.",
                   "Cuisez les spaghetti dans l'eau bouillante salée selon le temps indiqué.",
                   "Mélangez les pâtes à la sauce et servez avec du fromage râpé."],
        "astuce": "Gardez un peu d'eau de cuisson des pâtes pour lier la sauce.",
        "halal": "Bœuf haché certifié halal ; ni vin rouge ni lardons dans la sauce."},
    "Gratin Dauphinois": {
        "ingredients": [
            (800, "g", "pommes de terre", 2.10, 1.90),
            (25, "cl", "crème liquide", 1.30, 1.20),
            (25, "cl", "lait", 0.30, 0.28),
            (1, "gousse", "ail", 0.15, 0.15),
            (60, "g", "emmental râpé à présure végétale", 1.80, 1.60),
            (1, "noix", "beurre", 0.15, 0.14)],
