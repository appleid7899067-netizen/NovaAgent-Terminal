import os

def process_user_input(user_id):
    # ช่องโหว่: OS Command Injection
    os.system("echo " + user_id)
    
    # ช่องโหว่: Hardcoded secret
    key = "SUPER_SECRET_TOKEN_12345"
    return f"Processing {user_id} with {key}"
