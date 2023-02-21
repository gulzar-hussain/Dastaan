
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


data = [
        
     
    {
    "name": "Habib Bank Plaza, Karachi",
    "description": "This iconic building was built in 1963 and was the tallest building in South Asia at the time of its completion. It served as the headquarters of Habib Bank, one of the largest banks in Pakistan, until the early 2000s. The building is now a commercial and office space, and is considered a symbol of Karachi's modern architecture and urban landscape."
}

    ]





add_location = '''
INSERT INTO locations (longitude,latitude,location,description) VALUES (%s, %s, %s,%s) ON CONFLICT (longitude,latitude) DO NOTHING
'''
for place in data:
  conn, cur = get_db_connection()
  location = place['name']
  description = place['description']

  loc = getLocation(location)
  loc_values = (loc.longitude, loc.latitude, location,description)

  cur.execute(add_location, loc_values)
  conn.commit()
  cur.close()
  conn.close()

            # inserts a user
            
            # INSERT_USER = '''INSERT INTO users (username, first_name, last_name, password) VALUES (%s,%s,%s,crypt(%s,gen_salt('bf',8)))'''
            # USERS_DETAILS = ()
            # cur.execute(INSERT_USER,USERS_DETAILS)
            