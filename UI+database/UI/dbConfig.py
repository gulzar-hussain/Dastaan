
'''
______________________ ____________________
\__    ___/\_   _____//   _____/\__    ___/
  |    |    |    __)_ \_____  \   |    |   
  |    |    |        \/        \  |    |   
  |____|   /_______  /_______  /  |____|   
                   \/        \/            

'''

import psycopg2 , psycopg2.extras
from geopy.geocoders import Nominatim
def get_db_connection():
    try:
      conn = None
      conn = psycopg2.connect(
          database='mydastaan',
          user='postgres',
          password='google',
          host='localhost',
          port='5432',
          
      )
      cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
      return conn, cur
    except Exception as error:
      print(error)


def get_location_coordinates(address,d):
    geolocator = Nominatim(user_agent="dastaan")
    location = geolocator.geocode(address)
    print(location)
    if location is not None:
        conn, cur = get_db_connection()
        cur.execute("INSERT INTO locations (longitude, latitude,location, description, location_data) VALUES (%s, %s,%s, %s,ST_SetSRID(ST_GeomFromText('POINT(' || %s || ' ' || %s || ')'), 4326)) ON CONFLICT DO NOTHING RETURNING id", (location.longitude, location.latitude,address,d, location.longitude, location.latitude))
        address =address.lower()
        cur.execute("SELECT id from locations WHERE longitude ::numeric = %s AND latitude ::numeric = %s",(location.longitude,location.latitude))
        location_id = cur.fetchone()[0]
        cur.close()
        conn.commit()
        conn.close()
        return location_id
    else:
        return None


def get_nearby_stories(location):
  geolocator = Nominatim(user_agent="dastaan")
  location = geolocator.geocode(location)       
  if location is not None:
    conn, cur = get_db_connection()
    long = location.longitude
    lat = location.latitude
    query= '''
    SELECT description FROM stories WHERE location_id IN (
    SELECT id
    FROM locations WHERE ST_DWithin(
      location_data, 
      ST_SetSRID(ST_MakePoint(%s, %s), 4326), 
      10000
      )) AND location_id != (
    SELECT id
    FROM locations WHERE location_data = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
    ) ORDER BY year DESC;'''
    values = (long,lat,long,lat)
    cur.execute(query,values)
    nearby_stories = cur.fetchall()
    print(nearby_stories)
    cur.close()
    conn.close()
    
# get_nearby_stories('Empress Market')