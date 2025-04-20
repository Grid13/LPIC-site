from flask import Blueprint, render_template, request
from app.logic import get_marks, get_exos

main = Blueprint("main", __name__)

@main.route('/')
def home():
    return render_template("home.html", marks=get_marks())

@main.route('/render', methods=["GET", "POST"])
def render_view():
    if request.method == "POST":
        # gestion du fichier
        pass
    return render_template("form.html", exos=get_exos())

@main.route('/projects')
def projects():
    return render_template("projects.html")

@main.route('/contact')
def contact():
    return render_template("contact.html")

@main.app_errorhandler(404)
def error_404(e): return render_template("404.html"), 404

@main.app_errorhandler(500)
def error_500(e): return render_template("500.html"), 500
