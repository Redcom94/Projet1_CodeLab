import streamlit as st
from datetime import datetime
from base import ouvrir_base

st.title("Partage de frais")

# --- 1. LECTURE DE TOUTES LES DONNÉES ---
with ouvrir_base() as conn:
    groupes = conn.execute("SELECT id, nom, date_debut, date_fin FROM groupes").fetchall()
    membres = conn.execute("SELECT id, nom, groupe_id FROM membres").fetchall()
    depenses = conn.execute("SELECT id, groupe_id, libelle, type_depense, montant_centimes, payeur_id, date FROM depenses").fetchall()
    participants = conn.execute("SELECT depense_id, membre_id FROM participants").fetchall()

# --- 1.5 CALCUL DES SOLDES ---
# Initialisation des soldes à 0 pour tous les membres
soldes = {membre["id"]: 0 for membre in membres}

for depense in depenses:
    # 1. Le payeur est remboursé de la totalité (solde positif)
    soldes[depense["payeur_id"]] += depense["montant_centimes"]
    
    # 2. Récupération des participants pour cette dépense
    parts = [p["membre_id"] for p in participants if p["depense_id"] == depense["id"]]
    
    if parts:
        nb_parts = len(parts)
        part_de_base = depense["montant_centimes"] // nb_parts
        reste = depense["montant_centimes"] % nb_parts
        
        # 3. Chaque participant voit son solde diminuer de sa part
        for i, membre_id in enumerate(parts):
            soldes[membre_id] -= part_de_base
            # Le(s) premier(s) participant(s) absorbe(nt) le(s) centime(s) restant(s)
            if i < reste:
                soldes[membre_id] -= 1

# --- 2. AFFICHAGE DES GROUPES ET LEURS MEMBRES ---
st.header("Groupes et Membres")
for groupe in groupes:
    st.subheader(f"Groupe : {groupe['nom']}")
    for membre in membres:
        if groupe["id"] == membre["groupe_id"]:
            # Affichage du membre avec son solde calculé (formaté en euros)
            solde_euros = soldes[membre["id"]] / 100
            st.markdown(f"**{membre['nom']}** : solde de **{solde_euros:+.2f} €**")
            
            # Détail des dépenses payées par ce membre
            for depense in depenses:
                if depense["payeur_id"] == membre["id"]:
                    st.write(f"- A payé : {depense['libelle']} ({depense['montant_centimes'] / 100:.2f} €)")

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
            [groupe_id + 1, groupe_nom, str(date_de_debut), str(date_de_fin)]
        )
    st.rerun()

st.divider()

# --- 4. GESTION DES MEMBRES ---
st.header("Ajouter / Assigner un membre")

nom_nouveau_membre = st.text_input("Nom du nouveau membre")
nom_groupe_creation = st.selectbox("Assigner au groupe", [g["nom"] for g in groupes], key="creation_membre")
if st.button("Créer le membre") and nom_nouveau_membre:
    groupe_id_cible = next(g["id"] for g in groupes if g["nom"] == nom_groupe_creation)
    with ouvrir_base() as conn:
        nom_membre_ok = True
        for membre in membres:
            if nom_nouveau_membre == membre["nom"]:
                if groupe_id_cible == membre["groupe_id"]:
                    nom_membre_ok = False
        if nom_membre_ok == False:
            st.error("Erreur : deux membres du groupe ne peuvent pas avoir le même nom")
        else:
            conn.execute("INSERT INTO membres (groupe_id, nom) VALUES (?, ?)", [groupe_id_cible, nom_nouveau_membre])
    if nom_membre_ok:
        st.rerun()

if membres and groupes:
    nom = st.selectbox("Sélectionner un membre à assigner", [m["nom"] for m in membres])
    nom_groupe_cible = st.selectbox("Sélectionner le groupe", [g["nom"] for g in groupes])

    if st.button("Assigner au groupe"):
        nom_membre_ok = True
        groupe_id_cible = next(g["id"] for g in groupes if g["nom"] == nom_groupe_cible)
        for membre in membres:
            if nom == membre["nom"]:
                if groupe_id_cible == membre["groupe_id"]:
                    nom_membre_ok = False
        with ouvrir_base() as conn:
            if nom_membre_ok == False:
                st.error("Erreur : deux membres du groupe ne peuvent pas avoir le même nom")
            else:
                conn.execute("UPDATE membres SET groupe_id = ? WHERE nom = ?", [groupe_id_cible, nom])
            
        if nom_membre_ok:
            st.rerun()

st.divider()

# --- 5. GESTION DES DÉPENSES ---
st.header("Dépenses")

for depense in depenses:
    st.write(f"{depense['libelle']} - {depense['montant_centimes']/100:.2f} € - Type :{depense['type_depense']}")
    if st.button("Supprimer", key=f"dep_{depense['id']}"): 
        with ouvrir_base() as conn:
            conn.execute("DELETE FROM participants WHERE depense_id = ?", [depense["id"]])
            conn.execute("DELETE FROM depenses WHERE id = ?", [depense["id"]])
        st.rerun()

st.subheader("Ajouter une dépense")
if membres and groupes:
    nom_depense = st.text_input("Libellé de la dépense")
    type_depense = st.text_input("Type de la dépense")
    montant_centimes = st.number_input("Montant (en centimes)", min_value=0, step=100)
    date_depense = st.date_input("Date de la dépense")

    nom_groupe_depense = st.selectbox("Groupe concerné", [g["nom"] for g in groupes], key="grp_dep")
    
    # Filtrer les membres appartenant au groupe sélectionné
    grp_id = next(g["id"] for g in groupes if g["nom"] == nom_groupe_depense)
    membres_du_groupe = [m for m in membres if m["groupe_id"] == grp_id]
    
    nom_membre_payeur = st.selectbox("Payeur", [m["nom"] for m in membres_du_groupe], key="mem_dep")
    noms_participants = st.multiselect("Participants", [m["nom"] for m in membres_du_groupe])

    if st.button("Ajouter la dépense"):
        # Vérification 1 : Montant positif
        if montant_centimes <= 0:
            st.error("Le montant de la dépense doit être strictement positif (supérieur à 0).")
        # Vérification 2 : Au moins un participant
        elif not noms_participants:
            st.error("Il faut au moins un participant pour cette dépense.")
        # Vérification 3 : Le libellé ne doit pas être vide
        elif not nom_depense:
            st.error("Veuillez entrer un libellé pour la dépense.")
        elif not type_depense:
            st.error("Veuillez entrer un type pour la dépense.")
        else:
            groupe_selectionne = next(g for g in groupes if g["id"] == grp_id)
            date_depense_str = str(date_depense)
            
            # Vérification 4 : Date comprise dans le séjour
            if not (groupe_selectionne["date_debut"] <= date_depense_str <= groupe_selectionne["date_fin"]):
                st.error(f"Refusée : La date doit être comprise entre le {groupe_selectionne['date_debut']} et le {groupe_selectionne['date_fin']}.")
            else:
                mem_id = next(m["id"] for m in membres_du_groupe if m["nom"] == nom_membre_payeur)
                
                with ouvrir_base() as conn:
                    # Insérer la dépense et récupérer son ID
                    cursor = conn.execute(
                        "INSERT INTO depenses (groupe_id, libelle, type_depense, montant_centimes, payeur_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                        [grp_id, nom_depense, type_depense, montant_centimes, mem_id, date_depense_str]
                    )
                    nouvelle_depense_id = cursor.lastrowid
                    
                    # Insérer les participants
                    for nom_part in noms_participants:
                        part_id = next(m["id"] for m in membres_du_groupe if m["nom"] == nom_part)
                        conn.execute(
                            "INSERT INTO participants (depense_id, membre_id) VALUES (?, ?)",
                            [nouvelle_depense_id, part_id]
                        )
                st.rerun()
else:
    st.info("Veuillez d'abord créer au moins un groupe et un membre pour ajouter une dépense.")

## Remboursement entre membres
st.divider()
st.header("Remboursements")
st.info("Un remboursement est enregistré comme une dépense du rembourseur vers le membre remboursé.")

if membres and groupes:
    # 1. Sélectionner le groupe pour le remboursement
    nom_groupe_remb = st.selectbox("Groupe concerné par le remboursement", [g["nom"] for g in groupes], key="grp_remb")
    grp_remb_id = next(g["id"] for g in groupes if g["nom"] == nom_groupe_remb)
    membres_du_groupe_remb = [m for m in membres if m["groupe_id"] == grp_remb_id]

    if len(membres_du_groupe_remb) >= 2:
        # 2. Sélectionner qui rembourse et qui reçoit
        col1, col2 = st.columns(2)
        with col1:
            nom_rembourseur = st.selectbox("Qui rembourse ? (Payeur)", [m["nom"] for m in membres_du_groupe_remb], key="rembourseur")
        with col2:
            # On empêche de se rembourser soi-même dans l'interface
            options_receveurs = [m["nom"] for m in membres_du_groupe_remb if m["nom"] != nom_rembourseur]
            nom_receveur = st.selectbox("Qui reçoit ? (Bénéficiaire)", options_receveurs, key="receveur")
        
        montant_remb_centimes = st.number_input("Montant à rembourser (en centimes)", min_value=0, step=100, key="montant_remb")
        date_remb = st.date_input("Date du remboursement", key="date_remb")

        if st.button("Enregistrer le remboursement"):
            if montant_remb_centimes <= 0:
                st.error("Le montant doit être strictement positif.")
            else:
                rembourseur_id = next(m["id"] for m in membres_du_groupe_remb if m["nom"] == nom_rembourseur)
                receveur_id = next(m["id"] for m in membres_du_groupe_remb if m["nom"] == nom_receveur)
                libelle_remb = f"Remboursement de {nom_rembourseur} à {nom_receveur}"
                
                with ouvrir_base() as conn:
                    # Enregistrer le remboursement comme une dépense payée par le rembourseur
                    cursor = conn.execute(
                        "INSERT INTO depenses (groupe_id, libelle, type_depense, montant_centimes, payeur_id, date) VALUES (?, ?, ?, ?, ?, ?)",
                        [grp_remb_id, libelle_remb, "Remboursement", montant_remb_centimes, rembourseur_id, str(date_remb)]
                    )
                    nouvelle_depense_id = cursor.lastrowid
                    
                    # Le seul "participant" (celui qui a coûté l'argent à ce moment-là) est celui qui reçoit le remboursement
                    conn.execute(
                        "INSERT INTO participants (depense_id, membre_id) VALUES (?, ?)",
                        [nouvelle_depense_id, receveur_id]
                    )
                st.success("Remboursement enregistré !")
                st.rerun()
    else:
        st.warning("Il faut au moins deux membres dans ce groupe pour effectuer un remboursement.")
else:
    st.info("Veuillez d'abord créer au moins un groupe et des membres.")