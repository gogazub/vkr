"""Simple script to check if Docker setup is correct"""
import os

def check_setup():
    """Check if Docker setup is correct"""
    errors = []
    
    # Check if Dockerfile exists
    if os.path.exists("Dockerfile"):
        print("[OK] Dockerfile found")
    else:
        errors.append("Dockerfile not found")
    
    # Check if docker-compose.yml exists
    if os.path.exists("docker-compose.yml"):
        print("[OK] docker-compose.yml found")
    else:
        errors.append("docker-compose.yml not found")
    
    # Check if .env.example exists
    if os.path.exists(".env.example"):
        print("[OK] .env.example found")
    else:
        errors.append(".env.example not found")
    
    # Check if requirements.txt exists
    if os.path.exists("requirements.txt"):
        print("[OK] requirements.txt found")
    else:
        errors.append("requirements.txt not found")
    
    # Check if Makefile exists
    if os.path.exists("Makefile"):
        print("[OK] Makefile found")
    else:
        errors.append("Makefile not found")
    
    if errors:
        print("\n[ERROR] Errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n[OK] Docker setup check passed!")
        print("\nNext steps:")
        print("  1. Start services: make start")
        print("  2. Or manually: docker-compose up --build")
        print("  3. Run tests: make test")
        print("  4. View logs: make logs")
        return True

if __name__ == "__main__":
    success = check_setup()
    exit(0 if success else 1)
