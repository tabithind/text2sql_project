import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from services.auth_service import AuthService
from services.user_service import UserService

def main():
    print("Generating mock data...")
    
    # 1. Create a mock admin
    print("Creating admin...")
    admin_res = AuthService.register_admin(
        prenom="Alice", 
        nom="Smith", 
        email="admin@example.com", 
        password="password123", 
        entreprise="TechCorp"
    )
    
    if admin_res['ok']:
        admin_id = admin_res['admin_id']
        print(f"Admin created successfully! (ID: {admin_id})")
        
        # 2. Create a mock user for this admin
        print("Creating user...")
        user_res = UserService.creer_utilisateur(
            admin_id=admin_id,
            prenom="Bob",
            nom="Johnson",
            email="user@example.com",
            password="password123"
        )
        
        if user_res['ok']:
            print("User created successfully!")
        else:
            print(f"Failed to create user: {user_res.get('erreur')}")
            
    else:
        print(f"Failed to create admin: {admin_res.get('erreur')}")
        if "Duplicate" in str(admin_res.get('erreur')):
            print("Admin already exists. Skipping creation.")

    print("\n--- TEST ACCOUNTS ---")
    print("Admin: admin@example.com / password123")
    print("User: user@example.com / password123")
    print("---------------------")

if __name__ == "__main__":
    main()
