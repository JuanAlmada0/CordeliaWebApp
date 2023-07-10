from flask import Blueprint, render_template


homeBp = Blueprint('home', __name__)


@homeBp.route('/')
@homeBp.route('/home')
def home():
    return render_template('home.html')