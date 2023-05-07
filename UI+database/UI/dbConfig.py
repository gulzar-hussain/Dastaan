
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
          database='testdastaan',
          user='postgres',
          password='google',
          host='localhost',
          port='5432',
          
      )
      cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
      return conn, cur
    except Exception as error:
      print(error)
# import os
# image_filenames = os.listdir('C:/Users/HU-Student/Documents/GitHub/Dastaan/UI+database/UI - Copy/static/uploads')
# print(image_filenames)
# conn, cur = get_db_connection()
# for filename in image_filenames:
#     with open(f'C:/Users/HU-Student/Documents/GitHub/Dastaan/UI+database/UI - Copy/static/uploads/{filename}', 'rb') as f:
#         image_data = f.read()
#     cur.execute('UPDATE images SET image_data = %s WHERE file_name = %s', (image_data, filename))
# conn.commit()

# # Read image data from file
# file_path = 'C:/Users/HU-Student/Downloads/frere hall.jpg'
# with open(file_path, 'rb') as f:
#     image_data = f.read()

# # Insert image into database
# query = "INSERT INTO st_images (file_name, image_data, uploaded_on, story_id) VALUES (%s, %s, NOW(), %s);"
# values = ('frere hall.jpg', image_data, 50)  # Change story_id to the appropriate value
# cur.execute(query, values)
# conn.commit()

# # Close the database connection
# cur.close()
# conn.close()