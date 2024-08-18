import secrets
import os


def read_secret_key(app):
    if not os.path.isfile("secret_key.txt"):
        print("Secret key not found. Automatically creating one. No action is required.")
        
        with open("secret_key.txt", "w") as f:
            f.write(gen_key())
    
    with open("secret_key.txt", "r") as f:
        app.config["SECRET_KEY"] = f.read()


def gen_key():
    return secrets.token_hex(32)


def main():
    print("Generating secret key...")
    
    with open("secret_key.txt", "w") as f:
        f.write(gen_key())
    
    print("Secret key generated and saved to secret_key.txt")