
'''
______________________ ____________________
\__    ___/\_   _____//   _____/\__    ___/
  |    |    |    __)_ \_____  \   |    |   
  |    |    |        \/        \  |    |   
  |____|   /_______  /_______  /  |____|   
                   \/        \/            

'''

import psycopg2 , psycopg2.extras
def get_db_connection():
    try:
      conn = None
      conn = psycopg2.connect(
          database='Mydastaan',
        user='postgres',
        password='mydastaan',
        host= 'dastaan.cdqhboxvfqyn.eu-north-1.rds.amazonaws.com', # ask Gulzar for IP
        port='5432'
          
      )
      cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
      return conn, cur
    except Exception as error:
      print(error)
