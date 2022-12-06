
'''
______________________ ____________________
\__    ___/\_   _____//   _____/\__    ___/
  |    |    |    __)_ \_____  \   |    |   
  |    |    |        \/        \  |    |   
  |____|   /_______  /_______  /  |____|   
                   \/        \/            

'''

# import psycopg2 , psycopg2.extras

# conn = None
# try:
#     with psycopg2.connect(
#         database = 'aztabiei',
#         user = 'aztabiei',
#         password = '4aVvI5GHQ70Mqbeo9wyKx-YUTrZ9tmUb',
#         host = 'satao.db.elephantsql.com',
#         port = '5432'
#         ) as conn:
    
#         with  conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur: 
#             query = 'ALTER TABLE stories ADD year INTEGER NOT NULL'
        
#             cur.execute(query)
#             # inserts a user
            
#             # INSERT_USER = '''INSERT INTO users (username, first_name, last_name, password) VALUES (%s,%s,%s,crypt(%s,gen_salt('bf',8)))'''
#             # USERS_DETAILS = ()
#             # cur.execute(INSERT_USER,USERS_DETAILS)
            
#             # inserts a moderator
#             # INSERT_MODERATOR = '''INSERT INTO moderator (username, first_name, last_name, password) VALUES (%s,%s,%s, crypt(%s,gen_salt('bf',8))) '''
#             # MODERATORS_DETAILS = ( )
#             # cur.execute(INSERT_MODERATOR,MODERATORS_DETAILS)
#             # query = 'SELECT * FROM users'
#             # cur.execute(query)
#             # for users in cur.fetchall():
#             #     print(users['username'],users['first_name']+" "+users['last_name'])
            
            
# except Exception as error:
#     print(error)
    
# finally:
#     if conn is not None:
#         conn.close()

# from geopy.geocoders import Nominatim

# address='Barcelona'
# geolocator = Nominatim(user_agent="Your_Name")
# location = geolocator.geocode(address)
# print(location.address)
# print((location.latitude, location.longitude))