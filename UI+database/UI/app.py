import base64
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
OPENAI_API_KEY=""  #ask hamna for openai key

def get_db_connection():

    conn = None
    conn = psycopg2.connect(
        database='Mydastaan',
        user='postgres',
        password='google',
        host= 'localhost', # ask Gulzar for IP
        port='5432'
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn, cur


app = Flask(__name__, template_folder='Template', static_folder="static")
app.secret_key = os.environ.get('APP_SECRET_KEY')
openai.api_key = OPENAI_API_KEY

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
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_location_coordinates(lat,lng,address):  
    if lat is not None:
        conn, cur = get_db_connection()
        cur.execute("INSERT INTO locations (longitude, latitude,location, location_data) VALUES (%s, %s,%s, ST_SetSRID(ST_GeomFromText('POINT(' || %s || ' ' || %s || ')'), 4326)) ON CONFLICT DO NOTHING",
                    (lng, lat, address.title(), lng, lat))
        conn.commit()
        
        # getting location id
        cur.execute("SELECT id from locations WHERE longitude ::numeric = %s AND latitude ::numeric = %s",
                    (lng, lat))
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
    )SELECT s.*, l.location, p.file_name as image_file_name,p.image_data
    FROM stories s
    JOIN locations l ON s.location_id = l.id
    LEFT JOIN (
        SELECT story_id, file_name, image_data
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
        WHERE ST_DWithin(location_data, (SELECT location_data FROM user_location), 5000)
    ) AND s.location_id != (
        SELECT id
        FROM locations 
        WHERE location_data = (SELECT location_data FROM user_location)
    )
    GROUP BY s.id, l.location, p.file_name, p.image_data
    ORDER BY s.year DESC;'''
    values = (location,)
    cur.execute(query, values)
    rows = cur.fetchall()
    # print(row)
    if rows is None:
        flash('No nearby stories found', 'searchstory_error')
    nearby_stories = []
    for row in rows:
        story = {
            'id': row[0],
            'tag': row[1],
            'description': row[2],
            'user_id': row[3],
            'location_id': row[4],
            'year': row[5],
            'is_verified': row[6],
            'contributor': row[7],
            'uploaded_on': row[8],
            'title': row[9],
            'location': row[10],
            'image': []}

        if row['image_data'] is not None:
            data_uri = base64.b64encode(row['image_data']).decode('utf-8')
            story['image'].append(data_uri)
        nearby_stories.append(story)
    
    cur.close()
    conn.close()
    return nearby_stories


@app.route("/", methods=['GET', 'POST'])
def dashboard():
    # latest story uploaded
    query1 ='''
        SELECT s.*, i.id AS image_id,i.image_data, i.file_name 
        FROM stories AS s
        INNER JOIN images AS i ON s.id = i.story_id
        WHERE s.is_verified = true
        ORDER BY s.uploaded_on DESC
        LIMIT 1;
    '''
    query2 ='''
        SELECT s.*, i.file_name AS image_file_name, i.image_data
        FROM stories s
        LEFT JOIN images i ON s.id = i.story_id
        WHERE s.is_verified = true 
        AND lower(s.tag) = 'historical'
        GROUP BY s.id, i.file_name ,i.image_data
        ORDER BY s.year ASC
        LIMIT 1;
    '''
    query3 ='''
        SELECT s.*, COUNT(v.id) AS visit_count, i.file_name AS image_file_name, i.image_data
        FROM stories s
        INNER JOIN story_visits v ON s.id = v.story_id
        LEFT JOIN (
            SELECT story_id, file_name, image_data
            FROM images p1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images p2
                WHERE p1.story_id = p2.story_id
            )
        ) i ON s.id = i.story_id
        WHERE s.is_verified = true
        GROUP BY s.id, i.file_name, i.image_data
        ORDER BY visit_count DESC
        LIMIT 5;
    '''
    try:
        conn, cur = get_db_connection()
        cur.execute(query1)
        # latest_story = cur.fetchone()
        row = cur.fetchone()
        # print(row)
        if row is None:
            return "Story not found"
        latest_story = {
            'id': row[0],
            'tag': row[1],
            'description': row[2],
            'user_id': row[3],
            'location_id': row[4],
            'year': row[5],
            'is_verified': row[6],
            'contributor': row[7],
            'uploaded_on': row[8],
            'title': row[9],
            'location': row[10],
            'image': []}
   
        if row['image_data'] is not None:
            data_uri = base64.b64encode(row['image_data']).decode('utf-8')
            latest_story['image'].append(data_uri)
        
        cur.execute(query2)
        # historic_story = cur.fetchone()
        row = cur.fetchone()
        # print(row)
        if row is None:
            return "Story not found"
        historic_story = {
            'id': row[0],
            'tag': row[1],
            'description': row[2],
            'user_id': row[3],
            'location_id': row[4],
            'year': row[5],
            'is_verified': row[6],
            'contributor': row[7],
            'uploaded_on': row[8],
            'title': row[9],
            'location': row[10],
            'image': []}
   
        if row['image_data'] is not None:
            data_uri = base64.b64encode(row['image_data']).decode('utf-8')
            historic_story['image'].append(data_uri)
        
        cur.execute(query3)
        # mostvisited = cur.fetchall()
        rows = cur.fetchall()
        # print(row)
        if rows is None:
            return "Story not found"
        mostvisited = []
        for row in rows:
            story = {
                'id': row[0],
                'tag': row[1],
                'description': row[2],
                'user_id': row[3],
                'location_id': row[4],
                'year': row[5],
                'is_verified': row[6],
                'contributor': row[7],
                'uploaded_on': row[8],
                'title': row[9],
                'location': row[10],
                'image': []}
    
            if row['image_data'] is not None:
                data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                story['image'].append(data_uri)
            mostvisited.append(story)
       
        conn.close()
    except Exception as error:
        print(error)
        
    if request.method == 'POST':
        location = request.form['location_name']
        print(location)
        try:
            conn, cur = get_db_connection()
                      
            query = '''
                SELECT s.*, l.location, i.file_name as image_file_name, i.image_data
                FROM stories s
                JOIN locations l ON s.location_id = l.id
                LEFT JOIN (
                    SELECT story_id, file_name, image_data -- add image_data to the SELECT statement
                    FROM images p1
                    WHERE uploaded_on = (
                        SELECT MAX(uploaded_on)
                        FROM images p2
                        WHERE p1.story_id = p2.story_id
                    )
                ) i ON s.id = i.story_id
                WHERE s.is_verified = true AND l.location = %s
                GROUP BY s.id, l.location, i.file_name, i.image_data;
   
                '''
            cur.execute(query, (location,))
            
            rows = cur.fetchall()
            # print(row)
        
            stories = []
            for row in rows:
                story = {
                    'id': row[0],
                    'tag': row[1],
                    'description': row[2],
                    'user_id': row[3],
                    'location_id': row[4],
                    'year': row[5],
                    'is_verified': row[6],
                    'contributor': row[7],
                    'uploaded_on': row[8],
                    'title': row[9],
                    'location': row[10],
                    'image': []}
        
                if row['image_data'] is not None:
                    data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                    story['image'].append(data_uri)
                stories.append(story)
            
            if len(stories) == 0:
                flash('No stories found', 'searchstory_error')
            
            nearbyStories = get_nearby_stories(location)
            conn.close()
            return render_template('searchlocations.html', data=stories, nearbyStories=nearbyStories, searchtext=location)
        except Exception as error:
            print(error)
        flash('No stories found','searchstory_error')
        return render_template('searchlocations.html')

    return render_template('index.html',latestStory = latest_story,historicStory = historic_story, mostvisited = mostvisited)

@app.route("/test")
def test():
    query3 ='''
        SELECT s.*, COUNT(v.id) AS visit_count, i.file_name AS image_file_name
        FROM stories s
        INNER JOIN story_visits v ON s.id = v.story_id
        LEFT JOIN (
            SELECT story_id, file_name
            FROM images p1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images p2
                WHERE p1.story_id = p2.story_id
            )
        ) i ON s.id = i.story_id
        WHERE s.is_verified = true
        GROUP BY s.id, i.file_name
        ORDER BY visit_count DESC
        LIMIT 5;
    '''
   
    conn, cur = get_db_connection()
       
    cur.execute(query3)
    mostvisited = cur.fetchall()
    conn.close()
    return render_template("accountsettings.html",mostvisited=mostvisited)
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


@app.route('/location/<int:story_id>/<int:flag>')
def viewstory(story_id, flag):
    print('view story: ',story_id)
    # Get the story from the database based on the story_id
    # Render the HTML page with the story data
    try:
        conn, cur = get_db_connection()
        cur.execute("SELECT s.*, l.location, i.file_name, i.image_data FROM stories s JOIN locations l ON s.location_id = l.id LEFT JOIN images i ON s.id = i.story_id WHERE s.id = %s", (story_id,))
        row = cur.fetchone()
        # print(row)
        if row is None:
            return "Story not found"
        story = {
            'id': row[0],
            'tag': row[1],
            'description': row[2],
            'user_id': row[3],
            'location_id': row[4],
            'year': row[5],
            'is_verified': row[6],
            'contributor': row[7],
            'uploaded_on': row[8],
            'title': row[9],
            'location': row[10],
            'images': []
        }
        while row is not None:
            if row[11] is not None:
                image = {
                    'file_name': row[11],
                    'data': row[12]
                }
                story['images'].append(image)
            row = cur.fetchone()
        images = []    
        for image in story['images']:
            if image['data'] is not None:
                data_uri = base64.b64encode(image['data']).decode('utf-8')
                images.append(data_uri)
                
  
        q = '''
            INSERT INTO story_visits (story_id, visited_at)
            SELECT s.id, NOW()
            FROM stories s
            WHERE s.is_verified = true AND s.id = %s;
        '''
        values = (story_id,)
        cur.execute(q, values)
        conn.commit()
        print('Visits count incremented')
        cur.close()
        conn.close()
        print('end of view')
        return render_template('viewstory.html', story=story, images=images, is_from_approve=flag)

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
        cur.execute("UPDATE stories SET is_verified = TRUE WHERE id = %s", (story_id,))
        conn.commit()
        flash("","approvestory_success")
        cur.close()
        conn.close()
        return redirect(url_for('approveStory'))
        # return render_template('approveStory.html')

    except Exception as error:
        print(error)

    return render_template('approveStory.html')

@app.route('/deleted/<int:story_id>')
# @login_required(role='moderator')
def deleted(story_id):
    # Get the story from the database based on the story_id
    # Render the HTML page with the story data
    try:
        conn, cur = get_db_connection()
        cur.execute("DELETE FROM images WHERE story_id = %s", (story_id,))
        conn.commit()
        cur.execute("DELETE FROM story_visits WHERE story_id = %s", (story_id,))
        conn.commit()
        cur.execute("DELETE FROM stories WHERE id = %s", (story_id,))
        conn.commit()
        flash("Story Deleted Successfully!","deletestory_success")
        cur.close()
        conn.close()
        return redirect(url_for('all_stories'))
        # return render_template('approveStory.html')

    except Exception as error:
        print(error)
        flash("Story Couln't not be deleted!","deletestory_error")

    return render_template('deleteStories.html')


@app.route("/searchlocations", methods=['POST', 'GET'])
def searchlocations():
    if request.method == 'POST':
        location = request.form['location_name']
        print(location)
        try:
            conn, cur = get_db_connection()
            query = '''
                SELECT s.*, l.location, i.file_name as image_file_name, i.image_data
                FROM stories s
                JOIN locations l ON s.location_id = l.id
                LEFT JOIN (
                    SELECT story_id, file_name, image_data -- add image_data to the SELECT statement
                    FROM images p1
                    WHERE uploaded_on = (
                        SELECT MAX(uploaded_on)
                        FROM images p2
                        WHERE p1.story_id = p2.story_id
                    )
                ) i ON s.id = i.story_id
                WHERE s.is_verified = true AND l.location = %s
                GROUP BY s.id, l.location, i.file_name, i.image_data;
            '''
            values = (location,)
            cur.execute(query, values)
            rows = cur.fetchall()
            # print(row)
            if rows is None:
                flash('No stories found', 'searchstory_error')
                print('no story')
            stories = []
            for row in rows:
                story = {
                    'id': row[0],
                    'tag': row[1],
                    'description': row[2],
                    'user_id': row[3],
                    'location_id': row[4],
                    'year': row[5],
                    'is_verified': row[6],
                    'contributor': row[7],
                    'uploaded_on': row[8],
                    'title': row[9],
                    'location': row[10],
                    'image': []}
        
                if row['image_data'] is not None:
                    data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                    story['image'].append(data_uri)
                stories.append(story)
                               
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
    try:
        user_id = session['user_id']
    except:
        flash('You must be logged in to upload a story', 'addstory_error')
        return redirect(url_for('dasboard'))

    if request.method == 'POST':
        year = request.form['timeline']
        tag = request.form['tag']
        location = request.form['location_name']
        lat = request.form['latitude']
        lng = request.form['longitude']
        description = request.form['story']
        contributor = request.form['contributor']
        title = request.form['title']

        try:
            
            location_id = get_location_coordinates(lat,lng,location)
            if location_id:
                print("Location added successfully!")
                if year:
                    add_story = '''INSERT INTO stories (tag,description,user_id,location_id,year,contributor,uploaded_on,title) VALUES 
                    (%s,%s ,%s, %s,%s,%s,NOW(),%s) RETURNING id'''
                    values = (tag, description, user_id,
                        location_id, year, contributor,title)
                else:
                    add_story = '''INSERT INTO stories (tag,description,user_id,location_id,contributor,uploaded_on,title) VALUES 
                    (%s,%s ,%s, %s,%s,NOW(),%s) RETURNING id'''
                    values = (tag, description, user_id,
                        location_id, contributor,title)
                cur.execute(add_story, values)
                '''get id of the story that is just inserted to stories table above'''
                story_id = cur.fetchone()[0]
                           
                conn.commit()
                files = request.files.getlist('files[]')
               
                if files and story_id:
                    try:
                        for file in files:
                            print(file.filename)
                            if file and allowed_file(file.filename):
                                # Extract relevant information from file object
                                filename = secure_filename(file.filename)
                                image_data = file.read()

                                # Insert image into database
                                query = "INSERT INTO images (file_name, image_data, uploaded_on, story_id) VALUES (%s, %s, NOW(), %s);"
                                values = (filename, image_data, story_id)  # Change story_id to the appropriate value
                                cur.execute(query, values)
                                conn.commit()
                                
                                flash('Story uploaded successfully! :)', 'addstory_success')
                    except psycopg2.Error as e:
                        conn.rollback()
                        flash('Story upload failed! :(', 'addstory_error')
                        print("Error: ", e)

        except psycopg2.Error as e:
            conn.rollback()
            flash('Story upload failed! :(', 'addstory_error')
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
            flash('Email is already registered, please use another email.', 'user_error')
            return redirect(url_for('dashboard'))
        elif user:
            flash('username already taken.', 'user_warning')
            return redirect(url_for('dashboard'))
        # Insert new user into database
        else:
            try:
                cur.execute('INSERT INTO users (username, email, password, first_name, last_name, is_moderator, is_verified) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (username, email, password_hash, first_name, last_name, is_moderator, is_verified))
                conn.commit()
                flash('Registration successful. Please check your email to verify your account.', 'user_success')
                return redirect(url_for('dashboard'))
            except psycopg2.Error as e:
                    conn.rollback()
                    flash('Registration Failed! :(', 'user_error')
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
                    flash('Login successful.', 'user_success')
                    conn.close()
                    
                    return redirect(url_for('dashboard'))

                else:
                    flash ('Invalid email or password.', 'user_error')
                    return redirect(url_for('dashboard'))
                    # return redirect(url_for('login'))
            else:
                flash ("Please verify your email first", 'user_error')
                
                return redirect(url_for('dashboard'))
                # return redirect(url_for('login'))
        else:
            flash('Invalid email or password.', 'user_error')
            
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
    flash("Logout successful!", "logout_success")
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
        if not unapprovedStories:flash('No Stories found', 'approvestory_error') 
        if not all_stories:flash('All Stories have been approved', 'approvestory_error') 

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
def receive_coordinates():
    if request.method == 'POST':
        data = request.get_json()
        lat = data['lat']
        lng = data['lng']
        # print(lat, lng)
        # Do something with the coordinates
    
    return jsonify({'message': 'Coordinates received'}) 
    
@app.route('/storiesviamap',methods=('GET','POST'))
def search_locations():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    print(lat, lng)
    print('search_location')
    # print(lat, lng)
    # Do something with the coordinates
    conn, cur = get_db_connection()
    query1 = '''
        SELECT s.*, l.location, p.file_name as image_file_name, p.image_data
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN (
            SELECT story_id, file_name, image_data
            FROM images p1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images p2
                WHERE p1.story_id = p2.story_id
            )
        ) p ON s.id = p.story_id
        WHERE s.is_verified = true 
        AND ST_Distance(l.location_data::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) <= 100
        GROUP BY s.id, l.location, p.file_name, p.image_data
        ORDER BY s.year DESC;
    '''
    query2 = '''
        SELECT s.*, l.location, p.file_name as image_file_name, p.image_data
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN (
            SELECT story_id, file_name, image_data
            FROM images p1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images p2
                WHERE p1.story_id = p2.story_id
            )
        ) p ON s.id = p.story_id
        WHERE s.is_verified = true 
        AND ST_Distance(l.location_data::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) BETWEEN 100 AND 5000
        GROUP BY s.id, l.location, p.file_name, p.image_data
        ORDER BY s.year DESC;
    '''
    values = (lng,lat)
    cur.execute(query1,values)
    rows = cur.fetchall()
    
    if rows is None:
        flash("No, Stories Found!","searchstory_error")
        print('no story')
    stories = []
    for row in rows:
        story = {
            'id': row[0],
            'tag': row[1],
            'description': row[2],
            'user_id': row[3],
            'location_id': row[4],
            'year': row[5],
            'is_verified': row[6],
            'contributor': row[7],
            'uploaded_on': row[8],
            'title': row[9],
            'location': row[10],
            'image': []}

        if row['image_data'] is not None:
            data_uri = base64.b64encode(row['image_data']).decode('utf-8')
            story['image'].append(data_uri)
        stories.append(story)
    if len(stories) == 0:
        flash("No, Stories Found For This  Particular Place!","searchstory_error")
    cur.execute(query2,values)
    rows = cur.fetchall()
        # print(row)
    if rows is None:
        print('no story')
    nearbyStories = []
    for row in rows:
        story = {
            'id': row[0],
            'tag': row[1],
            'description': row[2],
            'user_id': row[3],
            'location_id': row[4],
            'year': row[5],
            'is_verified': row[6],
            'contributor': row[7],
            'uploaded_on': row[8],
            'title': row[9],
            'location': row[10],
            'image': []}

        if row['image_data'] is not None:
            data_uri = base64.b64encode(row['image_data']).decode('utf-8')
            story['image'].append(data_uri)
        nearbyStories.append(story)
    print(lng,lat)
    if stories:
        location = stories[0]['location']
    location = ''
    conn.close()
        
    return render_template('searchlocations.html', data=stories, nearbyStories=nearbyStories, searchtext=location)

@app.route('/locationData', methods=('GET','POST')) 
def locationData(): 
    query1 = '''
        SELECT s.id, l.location,l.location_data,l.latitude,l.longitude, i.file_name AS image_file_name
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
        ORDER BY s.year DESC;
    '''
    conn, cur = get_db_connection()
    try:
        cur.execute(query1)
        
        data = cur.fetchall()  
        cur.close()
        conn.close()
        # Convert the data to a JSON response
        response = []
        for row in data:
            response.append({
                'story_id': row[0],
                'location': row[1],
                'location_data':row[2],
                'latitude': row[3],
                'longitude': row[4],
            })
        return jsonify(response)
        
        
        # return jsonify({'message': 'Coordinates received', 'data': allapprovedStories})

    except psycopg2.Error as e:
        conn.rollback()
        print("Error: ", e)
        return redirect(url_for('dasboard'))
@app.route('/userstories', methods=('GET','POST')) 
def user_stories():
    user_id = session['user_id']   
    
    # all approved stories
    query1 = '''
        SELECT s.*, l.location, i.file_name AS image_file_name,i.image_data
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (
            SELECT story_id, file_name, image_data
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
        SELECT s.*, l.location, i.file_name AS image_file_name, i.image_data
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (
            SELECT story_id, file_name, image_data
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
        
        rows = cur.fetchall()
        # print(row)
        if rows is None:
            flash("You don't have any stories","mystory_error")
            print('no story')
        approvedStories = []
        for row in rows:
            story = {
                'id': row[0],
                'tag': row[1],
                'description': row[2],
                'user_id': row[3],
                'location_id': row[4],
                'year': row[5],
                'is_verified': row[6],
                'contributor': row[7],
                'uploaded_on': row[8],
                'title': row[9],
                'location': row[10],
                'image': []}
    
            if row['image_data'] is not None:
                data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                story['image'].append(data_uri)
            approvedStories.append(story)
        
        cur.execute(query2,value) 
        rows = cur.fetchall()
        # print(row)
        if rows is None:
            flash("Your all stories have been approved :)","mystory_success")
            print('no story')
        unapprovedStories = []
        for row in rows:
            story = {
                'id': row[0],
                'tag': row[1],
                'description': row[2],
                'user_id': row[3],
                'location_id': row[4],
                'year': row[5],
                'is_verified': row[6],
                'contributor': row[7],
                'uploaded_on': row[8],
                'title': row[9],
                'location': row[10],
                'image': []}
    
            if row['image_data'] is not None:
                data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                story['image'].append(data_uri)
            unapprovedStories.append(story)
        cur.close()
        conn.close()
        return render_template("userStories.html", approved=approvedStories,unapproved = unapprovedStories)

    except psycopg2.Error as e:
        conn.rollback()
        print("Error: ", e)
        
@app.route('/allstories', methods=('GET','POST')) 
def all_stories():
        
    # all approved stories
    query1 = '''
        SELECT s.*, l.location, i.file_name AS image_file_name, i.image_data
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (
            SELECT story_id, file_name, image_data
            FROM images i1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images i2
                WHERE i1.story_id = i2.story_id
            )
        ) i ON s.id = i.story_id
        WHERE s.is_verified = true 
        ORDER BY s.year DESC;
    '''
    # all unapproved stories
    query2 = '''
        SELECT s.*, l.location, i.file_name AS image_file_name, i.image_data
        FROM stories s
        JOIN locations l ON s.location_id = l.id
        JOIN users u ON s.user_id = u.id
        LEFT JOIN (
            SELECT story_id, file_name, image_data
            FROM images i1
            WHERE uploaded_on = (
                SELECT MAX(uploaded_on)
                FROM images i2
                WHERE i1.story_id = i2.story_id
            )
        ) i ON s.id = i.story_id
        WHERE s.is_verified = false 
        ORDER BY s.year DESC;
    '''
    conn, cur = get_db_connection()
    try:
        cur.execute(query1)
        rows = cur.fetchall()
        # print(row)
        if rows is None:
            # flash("No stories found","deletestory_error")
            print('no story')
        approvedStories = []
        for row in rows:
            story = {
                'id': row[0],
                'tag': row[1],
                'description': row[2],
                'user_id': row[3],
                'location_id': row[4],
                'year': row[5],
                'is_verified': row[6],
                'contributor': row[7],
                'uploaded_on': row[8],
                'title': row[9],
                'location': row[10],
                'image': []}
    
            if row['image_data'] is not None:
                data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                story['image'].append(data_uri)
            approvedStories.append(story)
        cur.execute(query2) 
        
        rows = cur.fetchall()
        # print(row)
        if rows is None and approvedStories is None:
            flash("No stories found","deletestory_error")
            print('no story')
        unapprovedStories = []
        for row in rows:
            story = {
                'id': row[0],
                'tag': row[1],
                'description': row[2],
                'user_id': row[3],
                'location_id': row[4],
                'year': row[5],
                'is_verified': row[6],
                'contributor': row[7],
                'uploaded_on': row[8],
                'title': row[9],
                'location': row[10],
                'image': []}
    
            if row['image_data'] is not None:
                data_uri = base64.b64encode(row['image_data']).decode('utf-8')
                story['image'].append(data_uri)
            unapprovedStories.append(story)
        cur.close()
        conn.close()
        return render_template("deleteStories.html", approved=approvedStories,unapproved = unapprovedStories)

    except psycopg2.Error as e:
        conn.rollback()
        print("Error: ", e) 
        
@app.route('/updatestory/<int:story_id>', methods=('GET','POST')) 
def update_stories(story_id):
    q = '''
    SELECT s.*, l.location, i.file_name
    FROM stories s
    JOIN locations l ON s.location_id = l.id
    LEFT JOIN images i ON s.id = i.story_id
    WHERE s.id = %s;
    '''
    conn,cur = get_db_connection()
    try:
        cur.execute(q,(story_id,))
        updatestory = cur.fetchone()
        return render_template("updateStories.html", updatestory = updatestory)
    except psycopg2.Error as e:
        conn.rollback()
        print("Error: ",e)
    return render_template("updateStories.html")
@app.route('/update/<int:story_id>', methods=['POST', 'GET'])
def update(story_id):
    conn, cur = get_db_connection()
    try:
        user_id = session['user_id']
    except:
        flash('You must be logged in to update your story', 'updatestory_error')
        return redirect(url_for('dasboard'))

    if request.method == 'POST':
        year = request.form['timeline']
        tag = request.form['tag']
        location = request.form['location_name']
        lat = request.form['latitude']
        lng = request.form['longitude']
        description = request.form['story']
        contributor = request.form['contributor']
        title = request.form['title']
        user_id = session['user_id']
        
        try:
            location_id = get_location_coordinates(lat,lng,location)
            if location_id:
                print("Location updated successfully!")
            update_story = '''UPDATE stories 
                SET tag = %s,
                    description = %s, 
                    user_id = %s, 
                    location_id = %s,
                    year = COALESCE(NULLIF(%s, '')::integer, year), 
                    is_verified = false, 
                    contributor = COALESCE(%s, contributor), 
                    uploaded_on = NOW(),
                    title = %s                
                WHERE id = %s;
                '''
            values = (tag, description, user_id,
                location_id, year, contributor,title,story_id)
        
            cur.execute(update_story, values)                       
            conn.commit()
            flash('Story Updated Successfully! :)',"updatestory_success")
            files = request.files.getlist('files[]')
               
            if files and story_id:
                try:
                    for file in files:
                        print(file.filename)
                        if file and allowed_file(file.filename):
                            # Extract relevant information from file object
                            filename = secure_filename(file.filename)
                            image_data = file.read()

                            # Insert image into database
                            query = "INSERT INTO images (file_name, image_data, uploaded_on, story_id) VALUES (%s, %s, NOW(), %s);"
                            values = (filename, image_data, story_id)  # Change story_id to the appropriate value
                            cur.execute(query, values)
                            conn.commit()
                            
                            flash('Story uploaded successfully! :)', 'updatestory_success')
                            cur.close()
                            conn.close()
                except psycopg2.Error as e:
                    conn.rollback()
                    flash('Story update failed! :(', 'updatestory_error')
                    print("Error: ", e)
            # flash('Story updated successfully! :)', 'updatestory_success')
            return redirect(url_for('update_stories',story_id =story_id))
        except psycopg2.Error as e:
            conn.rollback()
            flash('Story update failed! :(', 'updatestory_error')
            print("Error: ", e)
            return redirect(url_for('update_stories',story_id =story_id))
          
    cur.close()
    conn.close()

    return redirect(url_for('update_stories',story_id =story_id))
if __name__ == "__main__":
    app.run(host='localhost', debug=True)
