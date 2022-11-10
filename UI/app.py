from flask import Flask 


app = Flask(__name__,template_folder='Template')
@app.route('/')

def welcome():
    return 'Hello World!'


import login
import dashboard
import location 
import personalstory