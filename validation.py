"""
Module de validation des données pour ZellePy
"""

import re

def valider_nom(nom: str) -> str:
    nom = nom.strip()
    if not nom.isalpha():
        raise ValueError("Le nom doit contenir uniquement des lettres (sans espaces ni caractères spéciaux).")
    if not (2 <= len(nom) <= 50):
        raise ValueError("Le nom doit contenir entre 2 et 50 caractères.")
    return nom.capitalize()

def valider_prenom(prenom: str) -> str:
    prenom = prenom.strip()
    if not prenom.isalpha():
        raise ValueError("Le prénom doit contenir uniquement des lettres (sans espaces ni caractères spéciaux).")
    if not (2 <= len(prenom) <= 50):
        raise ValueError("Le prénom doit contenir entre 2 et 50 caractères.")
    return prenom.capitalize()

def valider_telephone(telephone: str) -> str:
    """
    Valide que le numéro de téléphone correspond exactement à 8 chiffres,
    sans préfixe +509 ni espaces.
    Retourne la chaîne de 8 chiffres si valide.
    """
    telephone = telephone.strip().replace(" ", "")
    if not telephone.isdigit():
        raise ValueError("Le numéro de téléphone doit contenir uniquement des chiffres.")
    if len(telephone) != 8:
        raise ValueError("Le numéro de téléphone doit contenir exactement 8 chiffres.")
    return telephone

def valider_email(email: str) -> str:
    """
    Valide l'adresse email selon une expression régulière simple,
    retourne l'email en minuscules.
    """
    email = email.strip().lower()
    regex = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not re.match(regex, email):
        raise ValueError("Adresse email invalide.")
    return email

def valider_montant(montant) -> float:
    """
    Valide que le montant est un nombre décimal strictement positif.
    Retourne le montant sous forme float si valide.
    """
    try:
        montant_float = float(montant)
    except (ValueError, TypeError):
        raise ValueError("Montant invalide. Veuillez entrer un nombre.")

    if montant_float <= 0:
        raise ValueError("Le montant doit être strictement positif.")
    return montant_float
