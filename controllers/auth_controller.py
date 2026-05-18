from services.auth_service import AuthService

class AuthController:
    def __init__(self):
        pass

    def login_user(self, email: str, password: str) -> dict:
        if not email or not password:
            return {'ok': False, 'erreur': "L'email et le mot de passe sont requis."}
        return AuthService.login_utilisateur(email, password)

    def login_admin(self, email: str, password: str) -> dict:
        if not email or not password:
            return {'ok': False, 'erreur': "L'email et le mot de passe sont requis."}
        return AuthService.login_admin(email, password)

    def register_admin(self, prenom: str, nom: str, email: str, password: str, entreprise: str) -> dict:
        if not all([prenom, nom, email, password, entreprise]):
            return {'ok': False, 'erreur': "Tous les champs sont obligatoires."}
        return AuthService.register_admin(prenom, nom, email, password, entreprise)
