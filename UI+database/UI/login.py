# import bcrypt
# import psycopg2
# import psycopg2.extras
# def get_db_connection():
    
#     conn = None
#     conn = psycopg2.connect(
#         database='aztabiei',
#         user='aztabiei',
#         password='4aVvI5GHQ70Mqbeo9wyKx-YUTrZ9tmUb',
#         host='satao.db.elephantsql.com',
#         port='5432'
#     )
#     cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     return conn,cur

# def hash_password(password, salt):
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password


# def check_password(password, hashed_password, salt):
#     hashed_input = hash_password(password, salt)
#     return bcrypt.checkpw(hashed_input, hashed_password)

# # # When the user signs up
# # password = "password123"

# # hashed_password = hash_password(password, salt)
# # # Store the hashed_password and salt in the database

# # # When the user logs in
# # input_password = "password123"
# # # Retrieve the salt and hashed_password from the database for the user
# # if check_password(input_password, hashed_password, salt):
# #     print("Login successful.")
# # else:
# #     print("Login failed.")



# email = 'admin1@example.com'
# password = 'admin1'
        
# conn, cur = get_db_connection()
# query = '''
# SELECT password, salt FROM users
# WHERE email = %s;
# '''
# values = (email,)     



# cur.execute(query,values)
# conn.commit()
# rows = cur.fetchall()
# rows = rows[0]
# print('password',rows[0])
# print('salt',rows[1],type(rows[1]))
# sal = rows[1].encode('utf-8')
# if check_password(password, rows[0][0], sal):
#     print("Login successful.")
#     cur.close()
#     conn.close()
# else:
#     print("Login failed.")
#     print("incorrect email or password.")
#     cur.close()
#     conn.close()
        