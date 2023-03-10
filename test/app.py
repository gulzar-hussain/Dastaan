from flask import Flask, render_template
from flask_googlemaps import GoogleMaps
app = Flask(__name__, template_folder='Template', static_folder="static")


GoogleMaps(app)

@app.route('/')
def map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run()
