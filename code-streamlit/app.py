import streamlit as st
from base import ouvrir_base

st.title("Partage de frais")

# --- 1. LECTURE DE TOUTES LES DONNÉES ---
with ouvrir_base() as conn:
    groupes = conn.execute("SELECT id, nom FROM groupes").fetchall()
    # On sélectionne bien l'id, le nom et le groupe_id pour les membres
    membres = conn.execute("SELECT id, nom, groupe_id FROM membres").fetchall()
    depenses = conn.execute("SELECT id, groupe_id, libelle, montant_centimes, payeur_id FROM depenses").fetchall()

# --- 2. AFFICHAGE DES GROUPES ET LEURS MEMBRES (Votre 2ème code) ---
st.header("Groupes et Membres")
for groupe in groupes:
    st.subheader(f"Groupe : {groupe['nom']}")
    for membre in membres:
        if groupe["id"] == membre["groupe_id"]:
            st.write(f"- {membre['nom']}")

st.divider()

# --- 3. GESTION DES GROUPES ---
st.header("Créer un groupe")
with ouvrir_base() as conn:
    max_id = conn.execute("SELECT max(id) FROM groupes").fetchone()[0]
    groupe_id = int(max_id) if max_id is not None else 0

groupe_nom = st.text_input("Nom du nouveau groupe")
date_de_debut = st.date_input("Date de début")
date_de_fin = st.date_input("Date de fin")

if st.button("Ajouter le groupe") and groupe_nom:
    with ouvrir_base() as conn:
        conn.execute(
            "INSERT INTO groupes (id, nom, date_debut, date_fin) VALUES (?, ?, ?, ?)", 
            [groupe_id + 1, groupe_nom, str(date_de_debut), str(date_de_fin)] # str() pour éviter le DeprecationWarning
        )
    st.rerun()

st.divider()

# --- 4. GESTION DES MEMBRES ---
st.header("Ajouter / Assigner un membre")

# Ajouter un nouveau membre
nom_nouveau_membre = st.text_input("Nom du nouveau membre")
if st.button("Créer le membre") and nom_nouveau_membre:
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO membres (groupe_id, nom) VALUES (1, ?)", [nom_nouveau_membre])
    st.rerun()

# Assigner un membre existant à un groupe
if membres and groupes:
    nom = st.selectbox("Sélectionner un membre à assigner", [m["nom"] for m in membres])
    # On affiche le nom du groupe dans la liste, c'est plus lisible que l'ID
    nom_groupe_cible = st.selectbox("Sélectionner le groupe", [g["nom"] for g in groupes])
    
    if st.button("Assigner au groupe"):
        # On retrouve l'ID du groupe sélectionné
        groupe_id_cible = next(g["id"] for g in groupes if g["nom"] == nom_groupe_cible)
        with ouvrir_base() as conn:
            conn.execute("UPDATE membres SET groupe_id = ? WHERE nom = ?", [groupe_id_cible, nom])
        st.rerun()

st.divider()

# --- 5. GESTION DES DÉPENSES (Votre 1er code) ---
st.header("Dépenses")

# Liste et suppression des dépenses
for depense in depenses:
    st.write(depense["libelle"])
    if st.button("Supprimer", key=f"dep_{depense['id']}"): 
        with ouvrir_base() as conn:
            conn.execute("DELETE from depenses WHERE id = ?", [depense["id"]])
        st.rerun()

st.subheader("Ajouter une dépense")
if membres and groupes:
    nom_depense = st.text_input("Libellé de la dépense")
    montant_centimes = st.number_input("Montant (en centimes)", min_value=0, step=100)
    date_depense = st.date_input("Date de la dépense")

    nom_groupe_depense = st.selectbox("Groupe concerné", [g["nom"] for g in groupes], key="grp_dep")
    nom_membre_payeur = st.selectbox("Payeur", [m["nom"] for m in membres], key="mem_dep")

    if st.button("Ajouter la dépense") and nom_depense:
        # Récupération des IDs
        grp_id = next(g["id"] for g in groupes if g["nom"] == nom_groupe_depense)
        mem_id = next(m["id"] for m in membres if m["nom"] == nom_membre_payeur)

        with ouvrir_base() as conn:
            conn.execute(
                "INSERT INTO depenses (groupe_id, libelle, montant_centimes, payeur_id, date) VALUES (?, ?, ?, ?, ?)",
                [grp_id, nom_depense, montant_centimes, mem_id, str(date_depense)]
            )
        st.rerun()
else:
    st.info("Veuillez d'abord créer au moins un groupe et un membre pour ajouter une dépense.")
