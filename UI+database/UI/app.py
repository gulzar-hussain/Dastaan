import login
import dashboard
import location
import personalstory
from flask import Flask, render_template, abort, request
import psycopg2
import psycopg2.extras
from geopy.geocoders import Nominatim
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.trainers import ListTrainer

bot = ChatBot("DaastanGo")
trainer=ListTrainer(bot)
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


def getLocation(address):
    geolocator = Nominatim(user_agent="Your_Name")
    location = geolocator.geocode(address)
    print(location.address)
    print((location.latitude, location.longitude))
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
def login():
    return render_template('login.html')
@app.route('/dashboard')
def getdashboard():
    return render_template('dashboard.html')
@app.route('/location')
def getlocation():
    return render_template('location.html')
@app.route("/viewstory")
def getViewStory():
    return render_template('viewStory.html')
@app.route("/addstory")
def getAddStory():
    return render_template('addpersonalstory.html')
@app.route('/getstory', methods=['POST','GET'])
def getStory():
    if request.method == 'POST':
        year = request.form['year']
        tag = request.form['tags']
        location = request.form['location']
        # return render_template("viewStory.html")
    # if request.method == 'GET':
        conn, cur = get_db_connection()
        query = '''
        SELECT description FROM stories WHERE (year = %s AND tag = %s AND location_id = (SELECT id FROM locations WHERE location =  %s))
        '''
        values = (year, tag, location)
        cur.execute(query,values)
        data = cur.fetchall()
        if  len(data) == 0:
            data = [['No story found :(']]
        print(data)
        conn.commit()
        
        cur.close()
        conn.close()
        return render_template("viewStory.html",data = data)


@app.route('/add', methods=['POST'])
def AddStory():
    if request.method == 'POST':
        year = request.form['timeline']
        tag = request.form['tags']
        location = request.form['location']
        # attachment = request.form['attachment']
        description = request.form['description']
        conn, cur = get_db_connection()
        ### ADDS LOCATION
        add_location = '''
        INSERT INTO locations (longitude,latitude,location) VALUES (%s, %s, %s) ON CONFLICT (longitude,latitude) DO NOTHING
        '''
        loc = getLocation(location)

        loc_values = (loc.longitude, loc.latitude, location)
        
        cur.execute(add_location, loc_values)
        conn.commit()
        
        
        add_story = '''INSERT INTO stories (tag,description,user_id,location_id,year) VALUES 
        (%s,%s ,%s,(SELECT id FROM locations WHERE location = %s),%s)'''
        values = (tag, description,
                  '7de7367c-56f4-491f-9f91-38b1b693decc', location, year)
        cur.execute(add_story, values)
        conn.commit()

        cur.close()
        conn.close()
        return render_template('viewStory.html')

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return str(bot.get_response(userText))

if __name__ == "__main__":
    app.run(host='localhost', debug=True)
