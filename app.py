import os
import requests
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_super_secret_key_that_should_be_changed'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1509@localhost/movie_db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    """ מודל המשתמשים """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    watchlist = db.relationship('WatchlistMovie', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """ יוצר האש (hash) מהסיסמה ושומר אותו """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """ בודק אם הסיסמה שהוזנה תואמת להאש השמור """
        return check_password_hash(self.password_hash, password)

class WatchlistMovie(db.Model):
    """ מודל הסרטים ברשימת הצפייה """
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

TMDB_API_KEY = "2812834bee3ec8a0d4d55064d52c6c16"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def process_movie_results(movies):
    processed_list = []
    for movie in movies:
        if movie.get('overview'):
            year = movie.get('release_date', 'N/A')[:4]
            movie['release_year'] = year
            processed_list.append(movie)
    return processed_list

def get_popular_movies():
    popular_movies = []
    popular_url = f"{TMDB_BASE_URL}/movie/popular"
    for page in range(1, 6):
        params = {'api_key': TMDB_API_KEY, 'language': 'en-US', 'page': page}
        try:
            response = requests.get(popular_url, params=params)
            response.raise_for_status(); results = response.json().get('results', []); popular_movies.extend(results)
        except: break
    return process_movie_results(popular_movies)

def search_movies(query):
    """פונקציה לחיפוש סרטים לפי שאילתה ב-TMDB API"""
    search_url = f"{TMDB_BASE_URL}/search/movie"
    params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'en-US'}
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status(); search_results = response.json().get('results', []); return process_movie_results(search_results)
    except: return []


@app.route('/register', methods=['GET', 'POST'])
def register():
    """ דף הרשמה למשתמשים חדשים """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('שם משתמש כבר קיים, אנא בחר שם אחר.', 'danger')
            return redirect(url_for('register'))

        
        new_user = User(username=username)
        new_user.set_password(password) 
        db.session.add(new_user)
        db.session.commit()
        
        flash('ההרשמה בוצעה בהצלחה! אנא התחבר.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ דף התחברות """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id 
            session['username'] = user.username
            session['is_admin'] = user.is_admin 
            return redirect(url_for('index'))
        else:
            flash('שם משתמש או סיסמה שגויים.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_watchlist = WatchlistMovie.query.filter_by(user_id=user_id).all()
    
    context = { 'watchlist': user_watchlist, 'search_mode': False }
    
    if request.method == 'POST' and 'search_query' in request.form:
        query = request.form.get('search_query')
        if query: context['movies'] = search_movies(query); context['search_mode'] = True
    else: context['movies'] = get_popular_movies()

    return render_template('index.html', **context)

@app.route('/add', methods=['POST'])
def add_to_watchlist():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    tmdb_id = request.form.get('movie_id')
    title = request.form.get('movie_title')
    user_id = session.get('user_id')

    existing_movie = WatchlistMovie.query.filter_by(tmdb_id=tmdb_id, user_id=user_id).first()
    if not existing_movie:
        new_movie = WatchlistMovie(tmdb_id=tmdb_id, title=title, user_id=user_id)
        db.session.add(new_movie)
        db.session.commit()
    
    return redirect(url_for('index'))
#test comment
#Triggering pipeline again
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)