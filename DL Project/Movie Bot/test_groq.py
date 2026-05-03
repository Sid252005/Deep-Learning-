import app

print('Testing Groq connection...')
try:
    movies = app.get_movie_recommendations('Matrix', 'movie', 'Any Genre')
    print('✅ Success! Found movies:')
    for m in movies:
        print(f"- {m.get('title')} ({m.get('year')})")
except Exception as e:
    import traceback
    traceback.print_exc()
