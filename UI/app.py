import login
import dashboard
import location 
import personalstory
from flask import Flask, render_template, abort 


app = Flask(__name__,template_folder='Template')
class Location:
    def __init__(self, key, name, lat, lng):
        self.key  = key
        self.name = name
        self.lat  = lat
        self.lng  = lng

locations = (
    # TODO: dynamically pick loaction objects from here
    Location('frere',      'Frere Hall',   37.9045286, -122.1445772),
    Location('empress', 'Empress Market',            37.8884474, -122.1155922),
    Location('museum',     'National Museum', 37.9093673, -122.0580063)
)
location_by_key = {location.key: location for location in locations}
@app.route('/')

@app.route("/dashboard")
def dashboard(location_code):
    location=location_by_key.get(location_code)
    if location:
        return render_template('dashboard.html', location=location)
    else:
        abort(404)

if __name__ =="__main__":
    app.run(host='localhost', debug=True)

