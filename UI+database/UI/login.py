import bcrypt

def hash_password(password, salt):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def check_password(password, hashed_password, salt):
    hashed_input = hash_password(password, salt)
    return bcrypt.checkpw(hashed_input, hashed_password)

# When the user signs up
password = "password123"
salt = bcrypt.gensalt()
hashed_password = hash_password(password, salt)
# Store the hashed_password and salt in the database

# When the user logs in
input_password = "password123"
# Retrieve the salt and hashed_password from the database for the user
if check_password(input_password, hashed_password, salt):
    print("Login successful.")
else:
    print("Login failed.")
