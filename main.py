from database import (
    creer_tables, creer_utilisateur, trouver_utilisateur,
    mettre_a_jour_solde, effectuer_transaction_db, obtenir_historique
)
from datetime import datetime
import re

def afficher_menu():
    print("""
===== MENU PRINCIPAL =====
1. Créer un nouvel utilisateur
2. Effectuer une transaction
3. Consulter l'historique
4. Quitter
===========================
    """)

def valider_telephone(numero):
    if not re.fullmatch(r"\d{8}", numero):
        raise ValueError("Le numéro doit contenir exactement 8 chiffres.")
    return numero

def formater_telephone(numero):
    return f"+509 {numero[:2]} {numero[2:4]} {numero[4:6]} {numero[6:]}"

def valider_email(email):
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        raise ValueError("Adresse email invalide.")
    return email

def creer_utilisateur_interactif():
    print("\n--- Création d'un nouvel utilisateur ---")
    prenom = input("Prénom : ").strip()
    nom = input("Nom : ").strip()

    while True:
        try:
            tel_brut = valider_telephone(input("Téléphone (8 chiffres) : ").strip())
            telephone = formater_telephone(tel_brut)
            break
        except ValueError as e:
            print(f"❌ Erreur : {e}")

    while True:
        try:
            email = valider_email(input("Email : ").strip())
            break
        except ValueError as e:
            print(f"❌ Erreur : {e}")

    while True:
        try:
            solde = float(input("Solde initial (HTG) : "))
            if solde < 0:
                raise ValueError("Le solde doit être positif.")
            break
        except ValueError as e:
            print(f"❌ Erreur : {e}")

    creer_utilisateur(prenom, nom, telephone, email, solde)
    print(f"✅ Utilisateur {prenom} {nom} créé avec succès !")

def rechercher_utilisateur(role="utilisateur"):
    print(f"\n🔍 Rechercher {role} par :")
    while True:
        choix = input("1. Téléphone\n2. Email\nVotre choix : ").strip()
        if choix not in ['1', '2']:
            print("❌ Choix invalide.")
            continue

        try:
            if choix == '1':
                tel_brut = valider_telephone(input("Téléphone (8 chiffres) : ").strip())
                telephone = formater_telephone(tel_brut)
                utilisateur = trouver_utilisateur(telephone=telephone)
            else:
                email = valider_email(input("Email : ").strip())
                utilisateur = trouver_utilisateur(email=email)

            if utilisateur:
                print(f"✅ {role.capitalize()} trouvé : {utilisateur['prenom']} {utilisateur['nom']}")
                return utilisateur
            else:
                print("❌ Utilisateur non trouvé.")
        except ValueError as e:
            print(f"❌ Erreur : {e}")

def effectuer_transaction():
    print("\n--- Nouvelle transaction ---")
    expediteur = rechercher_utilisateur("expéditeur")
    print(f"💰 Solde : {expediteur['solde']:.2f} HTG")

    destinataire = rechercher_utilisateur("destinataire")

    while True:
        try:
            montant = float(input("Montant à envoyer (HTG) : "))
            if montant <= 0:
                print("❌ Le montant doit être > 0.")
            elif montant + (montant * 0.01) > expediteur['solde']:
                print("❌ Solde insuffisant.")
            else:
                break
        except ValueError:
            print("❌ Montant invalide.")

    if input("Confirmer la transaction ? (o/n) : ").lower() != 'o':
        print("❌ Transaction annulée.")
        return

    frais = montant * 0.01
    total_debit = montant + frais

    mettre_a_jour_solde(expediteur['id'], expediteur['solde'] - total_debit)
    mettre_a_jour_solde(destinataire['id'], destinataire['solde'] + montant)

    transaction = effectuer_transaction_db(
        expediteur_id=expediteur['id'],
        destinataire_id=destinataire['id'],
        montant=montant,
        frais=frais
    )

    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n✅ Transaction réussie ({montant:.2f} HTG)")

    print("\n📋 Détails de réception :")
    print("-" * 40)
    print(f"👤 Destinataire : {destinataire['prenom']} {destinataire['nom']}")
    print(f"📱 Téléphone    : {destinataire['telephone']}")
    print(f"📧 Email       : {destinataire['email']}")
    print(f"💵 Reçu        : {montant:.2f} HTG")
    print(f"🕒 Date        : {date_str}")
    print("-" * 40)

    recu_nom = f"recu_{transaction['id']}.txt"
    with open(recu_nom, "w", encoding="utf-8") as f:
        f.write("===== Reçu ZellePy =====\n")
        f.write(f"Date           : {date_str}\n")
        f.write(f"Montant        : {montant:.2f} HTG\n")
        f.write(f"Frais          : {frais:.2f} HTG\n")
        f.write(f"Expéditeur     : {expediteur['prenom']} {expediteur['nom']}\n")
        f.write(f"Destinataire   : {destinataire['prenom']} {destinataire['nom']}\n")
        f.write(f"Téléphone      : {destinataire['telephone']}\n")
        f.write(f"Email          : {destinataire['email']}\n")
        f.write("=========================\n")

    print(f"\n🧾 Reçu enregistré : {recu_nom}")

def afficher_historique():
    print("\n--- Historique des transactions ---")
    utilisateur = rechercher_utilisateur()

    historique = obtenir_historique(utilisateur['id'])
    if not historique:
        print("ℹ️ Aucun historique disponible.")
        return

    print(f"\n📄 Historique de {utilisateur['prenom']} {utilisateur['nom']} :")
    for trans in historique:
        type_trans = "ENVOI" if trans['type'] == "envoi" else "RÉCEPTION"
        print(f"\n[{trans['date']}] {type_trans} de {trans['montant']:.2f} HTG")
        print(f"Avec : {trans['autre_prenom']} {trans['autre_nom']}")
        print(f"Frais : {trans['frais']:.2f} HTG")
        print(f"Numéro : {trans['numero']}")
        print("-" * 40)

if __name__ == "__main__":
    creer_tables()
    while True:
        afficher_menu()
        choix = input("Votre choix : ").strip()
        if choix == "1":
            creer_utilisateur_interactif()
        elif choix == "2":
            effectuer_transaction()
        elif choix == "3":
            afficher_historique()
        elif choix == "4":
            print("👋 Merci d’avoir utilisé ZellePy.")
            break
        else:
            print("❌ Choix invalide.")
        input("\nAppuyez sur Entrée pour continuer...")
