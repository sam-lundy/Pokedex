from . import main
from flask import render_template, request, redirect, url_for
from flask_login import login_required


@main.route('/')
def home():
    return render_template('home.html')

#If user navigates to /home, will redirect to root
@main.route('/home')
def home_redirect():
    return redirect(url_for('main.home'))


@main.route('/about')
def about():
    return render_template('about.html')