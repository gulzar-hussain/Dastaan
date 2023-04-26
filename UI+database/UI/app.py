from flask import redirect
from flask_cors import CORS
import re
import requests
import openai
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from geopy.geocoders import Nominatim
from psycopg2 import connect, sql
from werkzeug.utils import secure_filename, send_from_directory
import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():

    conn = None
    conn = psycopg2.connect(
        database='mydastaan',
        user='postgres',
        password='google',
        # host='localhost',
        host = "10.20.6.185",
        port='5432'
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn, cur


app = Flask(__name__, template_folder='Template', static_folder="static")
app.secret_key = os.environ.get('APP_SECRET_KEY')
openai.api_key = os.environ.get('OPENAI_API_KEY')
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
CORS(app, methods=["POST"])
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
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_location_id(address):
    geolocator = Nominatim(user_agent="dastaan")
    location = geolocator.geocode(address)
    if location is not None:
        conn, cur = get_db_connection()
        cur.execute("SELECT id from locations WHERE longitude ::numeric = %s AND latitude ::numeric = %s",
                    (location.longitude, location.latitude))
        location_id = cur.fetchone()[0]
        cur.close()
        conn.commit()
        conn.close()
        return location_id
    else:
        return None


def get_location_coordinates(address):
    geolocator = Nominatim(user_agent="dastaan")
    location = geolocator.geocode(address)
    # place_name = location.raw['display_name'].split(',')[0]
    # place_name = str(place_name)
    # if 'Karachi' not in place_name: place_name+=+', Karachi'
    # print(place_name)
    # print('lat',location.latitude,' ','long',location.longitude)
    
    if location is not None:
        conn, cur = get_db_connection()
        cur.execute("INSERT INTO locations (longitude, latitude,location, location_data) VALUES (%s, %s,%s, ST_SetSRID(ST_GeomFromText('POINT(' || %s || ' ' || %s || ')'), 4326)) ON CONFLICT DO NOTHING",
                    (location.longitude, location.latitude, address.title(), location.longitude, location.latitude))
        conn.commit()
        
        # getting location id
        cur.execute("SELECT id from locations WHERE longitude ::numeric = %s AND latitude ::numeric = %s",
                    (location.longitude, location.latitude))
        location_id = cur.fetchone()[0]
        cur.close()
        
        conn.close()
        return location_id
    else:
        print("Failed in fetching location")
        return None


def get_nearby_stories(location):
    print('getting nearby stories....')
    conn, cur = get_db_connection()
    
    query = '''
    WITH user_location AS (
    SELECT location_data
    FROM locations
    WHERE location = %s
    )SELECT s.*, l.location, p.file_name as image_file_name
    FROM stories s
    JOIN locations l ON s.location_id = l.id
    LEFT JOIN (
        SELECT story_id, file_name
        FROM images p1
        WHERE uploaded_on  = (
            SELECT MAX(uploaded_on)
            FROM images p2
            WHERE p1.story_id = p2.story_id
        )
    ) p ON s.id = p.story_id
    WHERE s.is_verified = true 
    AND s.location_id IN (
        SELECT id
        FROM locations 
        WHERE ST_DWithin(location_data, (SELECT location_data FROM user_location), 10000)
    ) AND s.location_id != (
        SELECT id
        FROM locations 
        WHERE location_data = (SELECT location_data FROM user_location)
    )
    GROUP BY s.id, l.location, p.file_name
    ORDER BY s.year DESC;'''
    values = (location,)
    cur.execute(query, values)
    nearby_stories = cur.fetchall()
    cur.close()
    conn.close()
    return nearby_stories


@app.route("/", methods=['GET', 'POST'])
def dashboard():
    # latest story uploaded
    query1 ='''
        SELECT s.id, s.description, s.uploaded_on, i.id AS image_id, i.file_name
        FROM stories AS s
        INNER JOIN images AS i ON s.id = i.story_id
        WHERE s.is_verified = true
        ORDER BY s.uploaded_on DESC
        LIMIT 1;
    '''
    query2 ='''
        SELECT s.id, s.description, s.year, i.id AS image_id, i.file_name
        FROM stories AS s
        INNER JOIN images AS i ON s.id = i.story_id
        WHERE s.year = (SELECT MIN(year) FROM stories)
        ORDER BY s.id ASC
        LIMIT 1;
    '''
    query3 ='''
        SELECT * from images LIMIT 10;
    '''
    try:
        conn, cur = get_db_connection()
        cur.execute(query1)
        latest_story = cur.fetchone()
        # print("latest story",latest_story)
        
        cur.execute(query2)
        historic_story = cur.fetchone()
        
        cur.execute(query3)
        images = cur.fetchall()
        
        conn.close()
    except Exception as error:
        print(error)
        
    if request.method == 'POST':
        location = request.form['location_name']
        print(location)
        try:
            conn, cur = get_db_connection()
            # latest story uploaded
            cur.execute('SELECT * FROM stories ORDER BY uploaded_on DESC LIMIT 1;')
            latest_story = cur.fetchall()
            print(latest_story)
          
            query = '''
                    SELECT 
            stories.*, 
            locations.location, 
            (
                SELECT file_name 
                FROM images 
                WHERE images.story_id = stories.id 
                ORDER BY id ASC 
                LIMIT 1
            ) AS image_file_name
            FROM stories
            JOIN locations ON stories.location_id = locations.id
            WHERE stories.is_verified = true
            AND stories.location_id = %s'''
            values = (get_location_id(location),)
            cur.execute(query, values)
            stories = cur.fetchall()
            print(stories)
            nearbyStories = get_nearby_stories(location)
            conn.close()
            return render_template('searchlocations.html', data=stories, nearbyStories=nearbyStories, searchtext=location)
        except Exception as error:
            print(error)
        return render_template('searchlocations.html')

    return render_template('index.html',latestStory = latest_story,historicStory = historic_story, images = images)

@app.route("/test")
def test():
    return render_template("accountsettings.html")
@app.route("/autocomplete")
def autocomplete():
    term = request.args.get('term')
    conn, cur = get_db_connection()
    query = """
        SELECT location, SIMILARITY(location, %s) AS score 
        FROM locations 
        WHERE location ILIKE %s 
        ORDER BY score DESC
        LIMIT 10
    """
    values = (term, f"%{term}%")
    cur.execute(query, values)
    results1 = [{'label': row[0]} for row in cur.fetchall()]
    
    query = '''SELECT DISTINCT tag, SIMILARITY(tag, %s) AS score 
        FROM stories 
        WHERE tag ILIKE %s
        ORDER BY score DESC
        LIMIT 10'''
    values = (term, f"%{term}%")
    cur.execute(query, values)
    results2 = [{'label': row[0]} for row in cur.fetchall()]
    
    conn.close()
    return jsonify(results1,results2)


@app.route('/image/<filename>')
def get_image(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(filepath):
        print('file is here')
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, environ=request.environ)
    else:
        abort(404)


@app.route('/location/<int:story_id>/<int:flag>')
def getlocations(story_id, flag):
    # Get the story from the database based on the story_id
    # Render the HTML page with the story data
    try:
        conn, cur = get_db_connection()
        cur.execute("SELECT * FROM stories WHERE id = %s", (story_id,))
        story = cur.fetchone()
        contributor = story['contributor']
        if not contributor: 
            user_id = story['user_id']
            cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            contributor = cur.fetchone()[0]
            print(contributor)
        location_id = story['location_id']
        cur.execute("SELECT * FROM images WHERE story_id = %s", (story_id,))
        images = cur.fetchall()
        cur.execute(
            "SELECT UPPER(location) FROM locations WHERE id = %s", (location_id,))
        location = cur.fetchone()[0]
        print(location)
        cur.close()
        conn.close()

        return render_template('viewstory.html', story=story, images=images, Location_name=location, is_from_approve=flag,contributor = contributor)

    except Exception as error:
        print(error)

    return render_template('viewstory.html')


@app.route('/approved/<int:story_id>')
# @login_required(role='moderator')
def approved(story_id):
    # Get the story from the database based on the story_id
    # Render the HTML page with the story data
    try:
        conn, cur = get_db_connection()
        cur.execute(
            "UPDATE stories SET is_verified = TRUE WHERE id = %s", (story_id,))
        conn.commit()
        cur.close()
        conn.close()

        return render_template('approveStory.html')

    except Exception as error:
        print(error)

    return render_template('approveStory.html')


@app.route("/searchlocations", methods=['POST', 'GET'])
def searchlocations():
    if request.method == 'POST':
        location = request.form['location_name']
        print(location)
        try:
            conn, cur = get_db_connection()
            query = '''
                                SELECT s.*, l.location, i.file_name AS image_file_name
            FROM stories s
            JOIN locations l ON s.location_id = l.id
            LEFT JOIN (
                SELECT story_id, file_name
                FROM images i1
                WHERE uploaded_on = (
                    SELECT MAX(uploaded_on)
                    FROM images i2
                    WHERE i1.story_id = i2.story_id
                )
            ) i ON s.id = i.story_id
            WHERE s.is_verified = true 
            AND l.location = %s
            ORDER BY s.year DESC;'''
            values = (location,)
            cur.execute(query, values)
            stories = cur.fetchall()
            if len(stories) == 0:
                flash('No stories found', 'error')
            # print(stories)
            nearbyStories = get_nearby_stories(location)
            conn.close()
            return render_template('searchlocations.html', data=stories, nearbyStories=nearbyStories)
        except Exception as error:
            print(error)
    return render_template('searchlocations.html')


@app.route('/map')
def map():
    # return render_template("map.html")
    return redirect("http://127.0.0.1:8080",code=302)



@app.route('/addingStory', methods=['POST', 'GET'])
def addingStory():
    conn, cur = get_db_connection()
    now = datetime.now()
    try:
        user_id = session['user_id']
    except:
        flash('You must be logged in to upload a story', 'error')
        return redirect(url_for('dasboard'))

    if request.method == 'POST':
        year = request.form['timeline']
        tag = request.form['tag']
        location = request.form['location_name']
        description = request.form['story']
        contributor = request.form['contributor']
        title = request.form['title']

        try:
            
            location_id = get_location_coordinates(location)
            if location_id:
                print("Location added successfully!")
                if year:
                    add_story = '''INSERT INTO stories (tag,description,user_id,location_id,year,contributor,uploaded_on,title) VALUES 
                    (%s,%s ,%s, %s,%s,%s,%s,%s) RETURNING id'''
                    values = (tag, description, user_id,
                        location_id, year, contributor,now,title)
                else:
                    add_story = '''INSERT INTO stories (tag,description,user_id,location_id,contributor,uploaded_on,title) VALUES 
                    (%s,%s ,%s, %s,%s,%s,%s) RETURNING id'''
                    values = (tag, description, user_id,
                        location_id, contributor,now,title)
                cur.execute(add_story, values)
                '''get id of the story that is just inserted to stories table above'''
                story_id = cur.fetchone()[0]
                           
                conn.commit()
                files = request.files.getlist('files[]')
                # print(files)
                if files and story_id:
                    try:
                        for file in files:

                            if file and allowed_file(file.filename):
                                filename = secure_filename(file.filename)
                                filepath = os.path.join(
                                    app.config['UPLOAD_FOLDER'], filename)
                                file.save(filepath)
                                cur.execute("INSERT INTO images (file_name, uploaded_on, story_id) VALUES (%s, %s,%s)", [
                                            filename, now, story_id])
                                conn.commit()
                                flash('Story uploaded successfully! :)', 'success')
                    except psycopg2.Error as e:
                        conn.rollback()
                        flash('Story upload failed! :(', 'error')
                        print("Error: ", e)

        except psycopg2.Error as e:
            conn.rollback()
            flash('Story upload failed! :(', 'error')
            print("Error: ", e)
            return render_template('addUserStories.html')
        # image upload

        
                
        cur.close()
        conn.close()

    return render_template('addUserStories.html')

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
        em = cur.fetchone()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()

        if em:
            flash('Email is already registered, please use another email.', 'error')
            return redirect(url_for('dashboard'))
        elif user:
            flash('username already taken.', 'error')
            return redirect(url_for('dashboard'))
        # Insert new user into database
        else:
            try:
                cur.execute('INSERT INTO users (username, email, password, first_name, last_name, is_moderator, is_verified) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (username, email, password_hash, first_name, last_name, is_moderator, is_verified))
                conn.commit()
                flash('Registration successful. Please check your email to verify your account.', 'success')
                return redirect(url_for('dashboard'))
            except psycopg2.Error as e:
                    conn.rollback()
                    flash('Registration Failed! :(', 'error')
                    print("Error: ", e)
        

        # Generate email verification token
        # token = ts.dumps(email, salt='email-verify')

        # # Create email message
        # subject = 'Verify Your Email'
        # recipient = email
        # url = url_for('verify_email', token=token, _external=True)
        # html = render_template('verify_email.html', url=url)
        # message = Message(subject=subject, recipients=[recipient], html=html)

        # # Send email
        # mail.send(message)

                    

    return redirect(url_for('dashboard'))

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
            # Verify whether user is verified
            if user[7]:

                # Verify password hash
                if check_password_hash(user[4], password):
                    # Set session variables
                    session['user_id'] = user[0]
                    session['is_moderator'] = user[6]
                    session['is_verified'] = user[7]
                    session['username'] = user[1]
                    flash('Login successful.', 'success')
                    conn.close()
                    
                    return redirect(url_for('dashboard'))

                else:
                    flash ('Invalid email or password.', 'error')
                    return redirect(url_for('dashboard'))
                    # return redirect(url_for('login'))
            else:
                flash ("Please verify your email first", 'error')
                
                return redirect(url_for('dashboard'))
                # return redirect(url_for('login'))
        else:
            flash('Invalid email or password.', 'error')
            
            return redirect(url_for('dashboard'))
            # return redirect(url_for('login'))
    else:
        return redirect(url_for('dashboard'))


@app.route("/verify/<token>")
def verify_email(token):
    conn, cur = get_db_connection()

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
    session.clear()
    flash("Logout successful!", "success")
    return redirect(url_for("dashboard"))


def get_unapprovedStories(location):
    # run a query to select stories based on the user's location
    conn, cur = get_db_connection()
    cur.execute("SELECT * FROM stories WHERE is_verified = false AND location_id = (SELECT id from locations where location = %s) ", (location,))
    stories = cur.fetchall()
    cur.execute("SELECT * FROM stories WHERE is_verified = false")
    all_stories = cur.fetchall()
    cur.close()
    conn.close()
    return stories, all_stories


@app.route("/approveStory", methods=("GET", "POST"))
# @login_required(role='moderator')
def approveStory():
    if session['is_moderator']:
        flag = 1
        unapprovedStories, all_stories = get_unapprovedStories("")
        return render_template("approveStory.html", data=unapprovedStories, unapprovedStories=all_stories, flag=flag)
    abort(400)


@app.route("/unapprovedStories", methods=("GET", "POST"))
def unapprovedStories():
    flag = 1
    if request.method == "POST":
        location = request.form['location_name']
        unapprovedStories, all_stories = get_unapprovedStories(location)

        return render_template("approveStory.html", data=unapprovedStories, unapprovedStories=all_stories, flag=flag)
    else:
        return render_template("approveStory.html", flag=flag)
# Open ai chatbot


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

@app.route('/mapcoordinates', methods=('GET','POST'))
def receive_cgetoordinates():
    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    # Do something with the coordinates
    
    return jsonify({'message': 'Coordinates received'})
    # return redirect(url_for("dashboard"))   
@app.route('/userstories', methods=('GET','POST')) 
def user_stories():
    user_id = session['user_id']   
    
    # all approved stories
    query1 = '''
        SELECT s.*, l.location, i.file_name AS image_file_name
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (
            SELECT story_id, file_name
            FROM images i1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images i2
                WHERE i1.story_id = i2.story_id
            )
        ) i ON s.id = i.story_id
        WHERE s.is_verified = true 
        AND u.id = %s
        ORDER BY s.year DESC;
    '''
    # all unapproved stories
    query2 = '''
        SELECT s.*, l.location, i.file_name AS image_file_name
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (
            SELECT story_id, file_name
            FROM images i1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images i2
                WHERE i1.story_id = i2.story_id
            )
        ) i ON s.id = i.story_id
        WHERE s.is_verified = false 
        AND u.id = %s
        ORDER BY s.year DESC;
    '''
    value = (user_id,)
    conn, cur = get_db_connection()
    try:
        cur.execute(query1,value)
        
        approvedStories = cur.fetchall()  
        cur.execute(query2,value) 
        unapprovedStories = cur.fetchall()  
        cur.close()
        conn.close()
        return render_template("userStories.html", approved=approvedStories,unapproved = unapprovedStories)
    except psycopg2.Error as e:
        conn.rollback()
        print("Error: ", e)
    
if __name__ == "__main__":
    app.run(host='localhost', debug=True)
