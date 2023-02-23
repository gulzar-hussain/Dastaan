import dashboard
import location
import personalstory
from flask import Flask, render_template, abort, request, redirect, url_for
import psycopg2
import psycopg2.extras
from geopy.geocoders import Nominatim

from werkzeug.utils import secure_filename
import os
#import magic
import urllib.request
from datetime import datetime

# from chatterbot import ChatBot
# from chatterbot.trainers import ChatterBotCorpusTrainer
# from chatterbot.trainers import ListTrainer

# bot = ChatBot("DaastanGo")
# trainer=ListTrainer(bot)
# trainer.train(['What is your name?', 'DaastanGo'])
# trainer.train(['Can you tell me about Empress Market', 'Sure. what would you like to know about it' ])
# trainer.train(['its history', 'Empress Market'])
# trainer.train(['a personal story', 'Sorry, but currently we dont have any.'])
# trainer=ChatterBotCorpusTrainer(bot)
# trainer.train("chatterbot.corpus.english")
#!/usr/bin/python

def get_db_connection():
    
    conn = None
    conn = psycopg2.connect(
        database='aztabiei',
        user='aztabiei',
        password='4aVvI5GHQ70Mqbeo9wyKx-YUTrZ9tmUb',
        host='satao.db.elephantsql.com',
        port='5432'
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn,cur

app = Flask(__name__, template_folder='Template', static_folder="static")
app.secret_key = "caircocoders-ednalan"
'''
For uploading multiple images
'''
UPLOAD_FOLDER = 'C:/Users/HU-Student/Documents/GitHub/Dastaan/UI+database/UI/static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




def getLocation(address):
    geolocator = Nominatim(user_agent="Your_Name")
    location = geolocator.geocode(address)
    return location


# class Location:
#     def __init__(self, key, name, lat, lng):
#         self.key = key
#         self.name = name
#         self.lat = lat
#         self.lng = lng


# locations = (
#     # TODO: dynamically pick loaction objects from here
#     Location('frere',      'Frere Hall',   37.9045286, -122.1445772),
#     Location('empress', 'Empress Market',            37.8884474, -122.1155922),
#     Location('museum',     'National Museum', 37.9093673, -122.0580063)
# )
# location_by_key = {location.key: location for location in locations}


@app.route('/')
def getdashboard():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/location')
def getlocation():
    return render_template('location2.html')
@app.route("/viewstory")
def getViewStory():
    return render_template('viewStory.html')
@app.route("/addstory")
def getAddStory():
    return render_template('addpersonalstory.html')
@app.route("/searchlocations", methods=['POST','GET'])
def searchLocation():
    print('here')
    if request.method == 'POST':
        location = request.form['location_name']
        location = location.lower()
        print(location)
        try:
            conn, cur = get_db_connection()
            query = 'SELECT tag, description, year FROM stories WHERE location_id = (SELECT id FROM locations WHERE LOWER(location) = %s)'
            values = (location,)
            cur.execute(query, values)
            stories = cur.fetchone()
            print(stories)
            conn.close()
        except Exception as error:
            print(error)
    return render_template('searchlocations.html')

@app.route('/newuser', methods=['POST','GET'])
def addUser():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first']
        last_name = request.form['last']
        email = request.form['email']
        password = request.form['pswd']
        
        conn, cur = get_db_connection()
        query = '''
        INSERT INTO users (username , first_name ,last_name ,password,email)
        SELECT %s, %s, %s, %s, %s
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = %s);
        '''
        # salt = bcrypt.gensalt()
        # pswd = hash_password(password,salt)
        values = (username, first_name, last_name,password,email,email)
        try:
            cur.execute(query,values)
            conn.commit()
            cur.close()
            conn.close()
            return render_template("login.html")
        
        except:
            conn.rollback()
            print("Message ---> error")
            cur.close()
            conn.close()
            return render_template("login.html")

@app.route('/loginuser', methods=['POST','GET'])
def login_user():
    if request.method == 'POST':
        email = request.form['email1']
        password = request.form['pswd1']
        
        conn, cur = get_db_connection()
        query = '''
        SELECT password FROM users
        WHERE email = %s;
        '''
        values = (email,)     
        
        # return render_template("dashboard.html")
        try:
            cur.execute(query,values)
            conn.commit()
            pswd = cur.fetchone()
            if password == pswd[0]:
                print("Login successful.")
                cur.close()
                conn.close()
                return render_template("dashboard.html")
            else:
                print("Login failed.")
                print("incorrect email or password.")
                cur.close()
                conn.close()
                return render_template("login.html")
    
        except:
            conn.rollback()
            print("Query execution failed.")
            cur.close()
            conn.close()
            return render_template("login.html")
        

@app.route('/getstory', methods=['POST','GET'])
def getStory():
    if request.method == 'POST':
        year = request.form['year']
        tag = request.form['tags']
        location = request.form['location']
        
        conn, cur = get_db_connection()
        cur.execute("SELECT file_name FROM images WHERE file_name = 'Saeed_Manzil.jpg'")
        image = [row[0] for row in cur.fetchall()]
        print(image)
        query = '''
        SELECT description FROM stories WHERE (year = %s AND tag = %s AND location_id = (SELECT id FROM locations WHERE location =  %s))
        '''
        values = (year, tag, location)
        cur.execute("SELECT DISTINCT year FROM stories ORDER BY year DESC")
        years = [row[0] for row in cur.fetchall()]
        print(years)
        try:
            cur.execute(query,values)
            data = [row[0] for row in cur.fetchall()]
            if  len(data) == 0:
                data = [['No story found :(']]
            print(data)
            conn.commit()
            
            
            cur.close()
            conn.close()
            return render_template("viewStory.html",data = data, years=years, image = image)
        except:
            conn.rollback()
            print("failed.")
            cur.close()
            conn.close()
            return render_template("viewStory.html", years=years)
@app.route('/add', methods=['POST'])
def AddStory():
    if request.method == 'POST':
        year = request.form['timeline']
        tag = request.form['tags']
        location = request.form['location']
        description = request.form['description']
        conn, cur = get_db_connection()
        ### ADDS LOCATION
        
        
        
        add_story = '''INSERT INTO stories (tag,description,user_id,location_id,year) VALUES 
        (%s,%s ,%s,(SELECT id FROM locations WHERE location = %s),%s)'''
        values = (tag, description,
                  '7de7367c-56f4-491f-9f91-38b1b693decc', location, year)
        cur.execute(add_story, values)
        conn.commit()

        cur.close()
        conn.close()
        return render_template('viewStory.html')
    
@app.route("/upload",methods=["POST","GET"])
def upload():
    conn, cur = get_db_connection()
    now = datetime.now()
    
    print(now)
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        story_id = 12
        #print(files)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur.execute("INSERT INTO images (id, file_name, uploaded_on) VALUES (%s, %s,%s)",[story_id,filename, now])
                conn.commit()
            print(file)
        cur.close()  
        conn.close() 
        flash('File(s) successfully uploaded')    
    return redirect('/images')

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return str(bot.get_response(userText))

if __name__ == "__main__":
    app.run(host='localhost', debug=True)
