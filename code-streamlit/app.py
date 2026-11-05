import streamlit as st
from base import ouvrir_base

st.title("Partage de frais")

# Lecture des données
with ouvrir_base() as conn:
    membres = conn.execute("SELECT nom, id FROM membres").fetchall()
    depenses = conn.execute("SELECT id, groupe_id, libelle, montant_centimes, payeur_id FROM depenses").fetchall()
    groupes = conn.execute("SELECT id, nom FROM groupes").fetchall()

# --- Section des dépenses ---
for depense in depenses:
    st.write(depense["libelle"])
    if st.button("Supprimer", key=depense["id"]):  # Clé unique sur l'ID (les libellés peuvent être en double)
        with ouvrir_base() as conn:
            conn.execute("DELETE from depenses WHERE id = ?", [depense["id"]])
        st.rerun()

st.header("Ajouter une dépense")
nom_depense = st.text_input("Libellé de la dépense")
montant_centimes = st.number_input("Montant (en centimes)", min_value=0, step=100)
date_depense = st.date_input("Date de la dépense")

# Correction : Création de listes pour les selectbox
noms_groupes = [groupe["nom"] for groupe in groupes]
nom_groupe = st.selectbox("Nom du groupe", noms_groupes)

noms_membres = [membre["nom"] for membre in membres]
nom_membre = st.selectbox("Nom du payeur", noms_membres)

if st.button("Ajouter dépense") and nom_depense:
    # Récupération des IDs correspondants
    groupe_id = next(g["id"] for g in groupes if g["nom"] == nom_groupe)
    membre_id = next(m["id"] for m in membres if m["nom"] == nom_membre)

    with ouvrir_base() as conn:
        conn.execute(
            "INSERT INTO depenses (groupe_id, libelle, montant_centimes, payeur_id, date) VALUES (?, ?, ?, ?, ?)",
            [groupe_id, nom_depense, montant_centimes, membre_id, date_depense]
        )
    st.rerun()

# --- Section des membres ---
st.header("Membres")
for membre in membres:
    st.write(membre["nom"])

# Exemple : ajoute un membre au groupe 1.
nom = st.text_input("Nom")
if st.button("Ajouter membre") and nom:
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO membres (groupe_id, nom) VALUES (1, ?)", [nom])
    st.rerun()