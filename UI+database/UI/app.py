import dashboard
import location
import personalstory
import openai
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from geopy.geocoders import Nominatim
from psycopg2 import connect, sql
from werkzeug.utils import secure_filename
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
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
app.secret_key = 'DastaanGo'
openai.api_key = "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"


# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False

# Initialize Flask-Mail
mail = Mail(app)

# Initialize URLSafeTimedSerializer
ts = URLSafeTimedSerializer(app.secret_key)

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

@app.route("/", methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        location = request.form['location_name']
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
            return render_template('searchlocations.html')
        except Exception as error:
            print(error)
        return render_template('searchlocations.html')
    return render_template('index.html')

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
def searchlocations():
    print('here')
    if request.method == 'POST':
        location = request.form['location_name']
        location = location.lower()
        print(location)
        try:
            conn, cur = get_db_connection()
            query = 'SELECT tag, description FROM stories WHERE location_id = (SELECT id FROM locations WHERE LOWER(location) = %s)'
            values = (location,)
            cur.execute(query, values)
            stories = cur.fetchall()
            print(stories)
            conn.close()
            return render_template('searchlocations.html',data = stories)
        except Exception as error:
            print(error)
    return render_template('searchlocations.html')



@app.route('/map')
def map():
    return render_template("map.html")


# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['pswd']
        first_name = request.form['first']
        last_name = request.form['last']
        is_moderator = False
        is_verified = False
        
        # Generate password hash
        password_hash = generate_password_hash(password)
        
        # Create cursor
        conn, cur = get_db_connection()

        # Check if email is already registered
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()

        if user:
            flash('Email is already registered, please use another email.', 'danger')
            return redirect(url_for('register'))

        # Insert new user into database
        cur.execute('INSERT INTO users (username, email, password, first_name, last_name, is_moderator, is_verified) VALUES (%s, %s, %s, %s, %s, %s, %s)', 
                    (username, email, password_hash, first_name, last_name, is_moderator, is_verified))
        conn.commit()

        # Generate email verification token
        token = ts.dumps(email, salt='email-verify')

        # Create email message
        subject = 'Verify Your Email'
        recipient = email
        url = url_for('verify_email', token=token, _external=True)
        html = render_template('verify_email.html', url=url)
        message = Message(subject=subject, recipients=[recipient], html=html)

        # Send email
        mail.send(message)

        flash('Registration successful. Please check your email to verify your account.', 'success')
        return redirect(url_for('login'))
    
    return render_template('login.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']

        # Create cursor
        conn, cur = get_db_connection()

        # Get user by email
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()

        if user:
            # Verify password hash
            if check_password_hash(user[4], password):
                # Set session variables
                session['user_id'] = user[0]
                session['is_moderator'] = user[6]
                session['is_verified'] = user[7]

                flash('Login successful.', 'success')
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route("/verify/<token>")
def verify_email(token):
    conn,cur = get_db_connection()
    
    cur.execute(sql.SQL("SELECT * FROM users WHERE token = {}").format(
        sql.Literal(token)
    ))
    user = cur.fetchone()
    
    if user:
        cur.execute(sql.SQL("UPDATE users SET is_verified = true, token = null WHERE id = {}").format(
            sql.Literal(user[0])
        ))
        conn.commit()
        flash("Email verification successful! You can now login.", "success")
    else:
        flash("Invalid token. Please contact support.", "danger")
    cur.close()
    conn.close()
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("is_moderator", None)
    flash("Logout successful!", "success")
    return redirect(url_for("home"))

    
    
    

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
    # if 'user_id' in session:
    #     return render_template('user_index.html')
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
        user_id = session['user_id']
        print(user_id)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur.execute("INSERT INTO images (id, file_name, uploaded_on) VALUES (%s, %s,%s)",[user_id,filename, now])
                conn.commit()
        cur.close()  
        conn.close() 
        flash('File(s) successfully uploaded')    
    return redirect('/addstory')

# @app.route("/get")
# def get_bot_response():
#     userText = request.args.get('msg')
#     return str(bot.get_response(userText))


#Open ai chatbot
@app.route("/guide", methods=("GET", "POST"))
def guide():
    if request.method == "POST":
        animal = request.form["animal"]
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=generate_prompt(animal),
            temperature=0.6,
        )
        return redirect(url_for("guide", result=response.choices[0].text))

    result = request.args.get("result")
    return render_template("guide.html", result=result)


def generate_prompt(animal):
    return """Where is this place?

Animal: Empress Market
Names: located in Saddar, Karachi, Pakistan

Animal: {}
Names:""".format(
        animal.capitalize()
    )

if __name__ == "__main__":
    app.run(host='localhost', debug=True)
