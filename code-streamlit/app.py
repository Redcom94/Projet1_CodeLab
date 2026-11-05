import streamlit as st

from base import ouvrir_base

st.title("Partage de frais")



# Ajoutez la suite de votre application ici.

#id nom date de début date de fin

# Lit les groupes 
with ouvrir_base() as conn:
    groupes = conn.execute("SELECT nom, id FROM groupes").fetchall()


# Lit les membres 
with ouvrir_base() as conn:
    membres = conn.execute("SELECT nom, groupe_id FROM membres").fetchall()


#Affiche les membres de chaque groupe
st.header("Groupes")
for groupe in groupes:
    st.write(groupe["nom"])
    #st.write(groupe["id"])
    st.header("Membres")
    for membre in membres:
        if (groupe["id"] == membre["groupe_id"]):
            st.write(membre["nom"])

#Créer un groupe 
groupe_id= int(conn.execute("SELECT max(id) FROM groupes").fetchone()[0])

groupe_nom = st.text_input("Nom du groupe")
date_de_debut= st.date_input("Date de début")
date_de_fin= st.date_input("Date de fin")

if st.button("Ajouter",key="ajouter_groupe") and groupe_nom:
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO groupes (id, nom, date_debut, date_fin) VALUES (?, ?, ?, ?)", [groupe_id+1,groupe_nom, date_de_debut, date_de_fin])
    st.rerun()

# Exemple : ajoute un membre au groupe n.
nom = st.selectbox("Ajouter un membre", [m["nom"] for m in membres])
groupe_id = st.selectbox("Groupe", [g["id"] for g in groupes])
if st.button("Ajouter un membre") and nom and groupe_id:
    with ouvrir_base() as conn:
        conn.execute("UPDATE membres SET groupe_id = ? WHERE nom = ?", [groupe_id, nom])
    st.rerun()

