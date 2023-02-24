
'''
______________________ ____________________
\__    ___/\_   _____//   _____/\__    ___/
  |    |    |    __)_ \_____  \   |    |   
  |    |    |        \/        \  |    |   
  |____|   /_______  /_______  /  |____|   
                   \/        \/            

'''

import psycopg2 , psycopg2.extras
from app import getLocation
def get_db_connection():
    try:
      conn = psycopg2.connect(
          database='aztabiei',
          user='aztabiei',
          password='4aVvI5GHQ70Mqbeo9wyKx-YUTrZ9tmUb',
          host='satao.db.elephantsql.com',
          port='5432'
      )
      cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
      return conn,cur
    except Exception as error:
      print(error)


'''
Search location databse retrival
'''
location = 'SAeED Manzil'
location = location.lower()
print(location)
try:
    conn, cur = get_db_connection()
    query = 'SELECT tag, description, year FROM stories WHERE location_id = (SELECT id FROM locations WHERE LOWER(location) = %s)'
    values = (location,)
    cur.execute(query, values)
    stories = cur.fetchall()
    print(stories)
    conn.close()
except Exception as error:
    print(error)