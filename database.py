import sqlite3
from datetime import datetime
import uuid

DB_NAME = "zellepy.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def creer_tables():
    conn = get_conn()
    c = conn.cursor()

    # Table utilisateurs
    c.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        telephone TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        solde REAL DEFAULT 0 CHECK (solde >= 0)
    )
    """)

    # Table transactions
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE NOT NULL,
        expediteur_id INTEGER NOT NULL,
        destinataire_id INTEGER NOT NULL,
        montant REAL NOT NULL CHECK (montant > 0),
        frais REAL NOT NULL CHECK (frais >= 0),
        date TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('envoi', 'reception')),
        FOREIGN KEY(expediteur_id) REFERENCES utilisateurs(id),
        FOREIGN KEY(destinataire_id) REFERENCES utilisateurs(id)
    )
    """)

    conn.commit()
    conn.close()

def creer_utilisateur(nom, prenom, telephone, email, solde=0):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO utilisateurs (nom, prenom, telephone, email, solde)
    VALUES (?, ?, ?, ?, ?)
    """, (nom, prenom, telephone, email, solde))
    conn.commit()
    user_id = c.lastrowid
    c.execute("SELECT * FROM utilisateurs WHERE id = ?", (user_id,))
    utilisateur = c.fetchone()
    conn.close()

    if utilisateur:
        return {
            "id": utilisateur[0],
            "nom": utilisateur[1],
            "prenom": utilisateur[2],
            "telephone": utilisateur[3],
            "email": utilisateur[4],
            "solde": utilisateur[5]
        }
    return None

def trouver_utilisateur(telephone=None, email=None):
    conn = get_conn()
    c = conn.cursor()
    utilisateur = None

    if telephone:
        c.execute("SELECT * FROM utilisateurs WHERE telephone = ?", (telephone,))
        utilisateur = c.fetchone()
    elif email:
        c.execute("SELECT * FROM utilisateurs WHERE email = ?", (email,))
        utilisateur = c.fetchone()

    conn.close()
    if utilisateur:
        return {
            "id": utilisateur[0],
            "nom": utilisateur[1],
            "prenom": utilisateur[2],
            "telephone": utilisateur[3],
            "email": utilisateur[4],
            "solde": utilisateur[5]
        }
    return None

def mettre_a_jour_solde(utilisateur_id, nouveau_solde):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE utilisateurs SET solde = ? WHERE id = ?", (nouveau_solde, utilisateur_id))
    conn.commit()
    conn.close()

def effectuer_transaction_db(expediteur_id, destinataire_id, montant, frais, type_trans='envoi'):
    conn = get_conn()
    c = conn.cursor()

    try:
        conn.execute("BEGIN TRANSACTION")

        # Vérifie le solde de l'expéditeur
        c.execute("SELECT solde FROM utilisateurs WHERE id = ?", (expediteur_id,))
        result = c.fetchone()
        if not result:
            raise ValueError("Expéditeur introuvable.")
        solde_expediteur = result[0]

        total_debit = montant + frais
        if solde_expediteur < total_debit:
            raise ValueError("Solde insuffisant pour effectuer la transaction.")

        # Débit expéditeur
        nouveau_solde_exp = solde_expediteur - total_debit
        c.execute("UPDATE utilisateurs SET solde = ? WHERE id = ?", (nouveau_solde_exp, expediteur_id))

        # Crédit destinataire
        c.execute("SELECT solde FROM utilisateurs WHERE id = ?", (destinataire_id,))
        result = c.fetchone()
        if not result:
            raise ValueError("Destinataire introuvable.")
        solde_destinataire = result[0]
        nouveau_solde_dest = solde_destinataire + montant
        c.execute("UPDATE utilisateurs SET solde = ? WHERE id = ?", (nouveau_solde_dest, destinataire_id))

        # Enregistrement transaction
        numero_transaction = str(uuid.uuid4())
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO transactions (numero, expediteur_id, destinataire_id, montant, frais, date, type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (numero_transaction, expediteur_id, destinataire_id, montant, frais, date, type_trans))

        conn.commit()

        return {
            "numero": numero_transaction,
            "date": date,
            "montant": montant,
            "frais": frais,
            "total_debit": total_debit,
            "solde_restant": nouveau_solde_exp
        }

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()

def obtenir_historique(utilisateur_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    SELECT t.numero, t.montant, t.frais, t.date,
           u1.prenom, u1.nom,
           u2.prenom, u2.nom,
           CASE WHEN t.expediteur_id = ? THEN 'envoi' ELSE 'reception' END AS type_trans
    FROM transactions t
    JOIN utilisateurs u1 ON t.expediteur_id = u1.id
    JOIN utilisateurs u2 ON t.destinataire_id = u2.id
    WHERE t.expediteur_id = ? OR t.destinataire_id = ?
    ORDER BY t.date DESC
    """, (utilisateur_id, utilisateur_id, utilisateur_id))

    rows = c.fetchall()
    conn.close()

    historique = []
    for r in rows:
        numero, montant, frais, date, exp_prenom, exp_nom, dest_prenom, dest_nom, type_trans = r
        autre_prenom, autre_nom = (dest_prenom, dest_nom) if type_trans == 'envoi' else (exp_prenom, exp_nom)

        historique.append({
            "numero": numero,
            "montant": montant,
            "frais": frais,
            "date": date,
            "type": type_trans,
            "autre_prenom": autre_prenom,
            "autre_nom": autre_nom,
        })
    return historique
