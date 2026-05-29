"""
Module de gestion des transactions ZellePy
"""

import uuid
from typing import Dict
import database
import validation

def generer_numero_transaction() -> str:
    """Génère un numéro de transaction unique au format ZELLE-XXXXXXXX (8 caractères hexadécimaux)."""
    return f"ZELLE-{uuid.uuid4().hex[:8].upper()}"

def calculer_frais(montant: float) -> float:
    """
    Calcule les frais de transaction selon le barème :
    - 0 HTG si montant <= 100 HTG
    - 1% du montant si 100 < montant <= 1000 HTG
    - 0.5% du montant si montant > 1000 HTG
    """
    if montant <= 100:
        return 0.0
    elif montant <= 1000:
        return round(montant * 0.01, 2)
    else:
        return round(montant * 0.005, 2)

def effectuer_transaction(expediteur_id: int, destinataire_info: str, montant: float) -> Dict:
    """
    Effectue une transaction d'argent entre deux utilisateurs.

    Parameters:
        expediteur_id (int): ID de l'expéditeur.
        destinataire_info (str): Email ou téléphone (8 chiffres) du destinataire.
        montant (float): Montant à transférer (doit être > 0).

    Returns:
        Dict: Détails de la transaction créée.

    Raises:
        ValueError: Si le destinataire n'existe pas, si le solde est insuffisant ou si le montant est invalide.
    """
    # Validation et recherche du destinataire
    if "@" in destinataire_info:
        # On valide l'email
        destinataire_email = validation.valider_email(destinataire_info)
        destinataire = database.trouver_utilisateur(email=destinataire_email)
    else:
        # On valide le téléphone et on formate +509 ########
        tel_brut = validation.valider_telephone(destinataire_info)
        telephone_formate = f"+509 {tel_brut}"
        destinataire = database.trouver_utilisateur(telephone=telephone_formate)

    if destinataire is None:
        raise ValueError("Destinataire non trouvé.")

    # Validation du montant
    montant_valide = validation.valider_montant(montant)

    # Calcul des frais
    frais = calculer_frais(montant_valide)

    # Recherche et vérification du solde de l'expéditeur
    expediteur = database.trouver_utilisateur(id=expediteur_id)
    if expediteur is None:
        raise ValueError("Expéditeur non trouvé.")
    if expediteur['solde'] < montant_valide + frais:
        raise ValueError("Solde insuffisant pour effectuer cette transaction.")

    # Génération du numéro unique de transaction
    numero = generer_numero_transaction()

    # Création de la transaction en base de données
    transaction = database.creer_transaction(
        numero=numero,
        montant=montant_valide,
        frais=frais,
        expediteur_id=expediteur_id,
        destinataire_id=destinataire['id']
    )

    # Mise à jour des soldes dans la base (expéditeur - total, destinataire + montant)
    nouveau_solde_expediteur = expediteur['solde'] - montant_valide - frais
    nouveau_solde_destinataire = destinataire['solde'] + montant_valide

    database.mettre_a_jour_solde(expediteur_id, nouveau_solde_expediteur)
    database.mettre_a_jour_solde(destinataire['id'], nouveau_solde_destinataire)

    return transaction
