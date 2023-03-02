
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
