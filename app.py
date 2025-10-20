import os
import requests
from flask import Flask, render_template, request

# ---- תצורה ----
# הגדרת אפליקציית Flask
app = Flask(__name__)

# הגדרת מפתח ה-API והכתובת הבסיסית של TMDB
# המפתח שלך שולב כאן
TMDB_API_KEY = "2812834bee3ec8a0d4d55064d52c6c16"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# רשימת צפייה "מדומה" שתשב בזיכרון. בפרויקט אמיתי זה יוחלף במסד נתונים.
watchlist = []

# ---- פונקציות עזר ----
def search_movies(query):
    """פונקציה לחיפוש סרטים לפי שאילתה ב-TMDB API"""
    search_url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'en-US'  # אפשר לשנות ל-'he' לקבלת תוצאות בעברית אם קיימות
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()  # יזרוק שגיאה אם הבקשה נכשלה
        search_results = response.json().get('results', [])
        return search_results
    except requests.exceptions.RequestException as e:
        print(f"Error searching for movies: {e}")
        return []

# ---- נתיבים (Routes) באפליקציה ----
@app.route('/', methods=['GET', 'POST'])
def index():
    """הדף הראשי: מציג את רשימת הצפייה ומאפשר חיפוש"""
    search_results = []
    if request.method == 'POST':
        query = request.form.get('search_query')
        if query:
            search_results = search_movies(query)

    return render_template('index.html', watchlist=watchlist, search_results=search_results)

@app.route('/add', methods=['POST'])
def add_to_watchlist():
    """מוסיף סרט לרשימת הצפייה"""
    movie_id = request.form.get('movie_id')
    movie_title = request.form.get('movie_title')
    
    # מונע כפילויות ברשימה
    if movie_id and movie_title and not any(m['id'] == movie_id for m in watchlist):
        watchlist.append({'id': movie_id, 'title': movie_title})
        
    # חוזרים לדף הבית לאחר הוספה
    return index()

# ---- הרצת האפליקציה ----
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)