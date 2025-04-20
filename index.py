import requests
import json
import os
import uuid
import shutil
import threading
import os
from threading import Thread
from orchestrateur import Orchestrateur
from time import sleep
from flask import Flask, request, render_template

app = Flask(__name__, template_folder='templates')
os.chdir(os.path.dirname(os.path.realpath(__file__)))
ALLOWED_EXTENSIONS = ['py','c']

@app.errorhandler(404)
def page_not_found(e):
   # note that we set the 404 status explicitly
   return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
   # note that we set the 500 status explicitly
   return render_template('500.html'), 500

def returnJson(content):
   status = content["status"]
   del content['status']
   response = app.response_class(
      response=json.dumps(content),
      status=status,
      mimetype='application/json'
   )
   return response

def allowed_file(filename):
   return '.' in filename and filename.split('.')[-1] in ALLOWED_EXTENSIONS

@app.route('/render', methods =["GET", "POST"])
def render():
   orchestrateur = Orchestrateur()
   if request.method == "POST":
      uuidMake = uuid.uuid1()
      json_receive = request.form.to_dict()
      json_receive["uuidMake"] = str(uuidMake)
      del json_receive["Send"]
      file = request.files['justification']
      if file and allowed_file(file.filename) and orchestrateur.if_login(json_receive):
         extension = file.filename.split('.')[-1]
         filename = f"{uuidMake}.{file.filename.split('.')[-1]}"
         os.mkdir("upload/" + json_receive["uuidMake"])
         file.save("upload/" + json_receive["uuidMake"] + "/" + filename)
         result =  True
         Thread(target=orchestrateur.lunch_correction,args=(json_receive, extension)).start()
      else:
         result =  False
      return render_template(f"render_result.html",result = result)
   return render_template("form.html", exos = orchestrateur.get_all_exercice())

@app.route('/', methods =["GET", "POST"])
def home():
   user = request.args.get('userid')
   marks = None
   if user:
      orchestrateur = Orchestrateur()
      marks = orchestrateur.all_mark_from_user(user)
      one = marks[0]["user"]
   else:
      orchestrateur = Orchestrateur()
      marks = orchestrateur.best_mark_by_exercice()
      one = None
   return render_template("home.html", marks=marks, one=one)

@app.route("/projects", methods=["GET"])
def projects():
   orchestrateur = Orchestrateur()
   return render_template("projects.html", projects_data=orchestrateur.get_all_project())

@app.route("/contact", methods=["GET"])
def contact():
   return render_template("contact.html")

if __name__=='__main__':
   app.run(debug = True)