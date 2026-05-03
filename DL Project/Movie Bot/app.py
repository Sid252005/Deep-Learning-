"""
🎬 Movie Recommendation + Review Bot
=====================================
Powered by Groq API + Gradio UI

How it works:
  - User enters a mood OR a movie they liked
  - Groq recommends 5 similar movies
  - Each movie gets a full AI-generated review + star rating
"""

import json
import gradio as gr
from openai import OpenAI

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

# Paste your Groq API key here
GROQ_API_KEY = "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"

# Configure Groq Client
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Model to use
MODEL = "llama-3.1-8b-instant"

# ──────────────────────────────────────────────────────────────────────────────
# CORE FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def get_movie_recommendations(user_input, input_type, genre_filter):
    """
    Calls Groq API to get 5 movie recommendations based on:
    - user_input   : mood (e.g. 'happy') OR movie name (e.g. 'Interstellar')
    - input_type   : 'mood' or 'movie'
    - genre_filter : preferred genre or 'Any'

    Returns: parsed JSON list of 5 movies
    """

    # Build the prompt based on input type
    if input_type == "🎭 I'm in a mood":
        context = f"The user is feeling: {user_input}"
        instruction = f"Recommend 5 movies that perfectly match this mood: '{user_input}'."
    else:
        context = f"The user loved the movie: {user_input}"
        instruction = f"Recommend 5 movies similar to '{user_input}' that fans of it would love."

    genre_instruction = ""
    if genre_filter and genre_filter != "Any Genre":
        genre_instruction = f"Focus on the {genre_filter} genre."

    prompt = f"""
You are an expert film critic and movie enthusiast.

{context}
{genre_instruction}

{instruction}

Return ONLY a valid JSON array (no explanation, no markdown, no code blocks).
Each movie object must follow this EXACT format:

[
  {{
    "title": "Movie Title",
    "year": 2023,
    "genre": "Genre1, Genre2",
    "director": "Director Name",
    "match_reason": "Why this movie matches the mood/preference in 1-2 sentences",
    "review": "A compelling 3-4 sentence AI-generated review of the movie",
    "rating": 4.5,
    "mood_tags": ["tag1", "tag2", "tag3"]
  }}
]

- rating must be a number between 1.0 and 5.0
- mood_tags: 3 short emotional/style tags like 'mind-bending', 'heartwarming', 'edge-of-seat'
- Return exactly 5 movies
- Return ONLY the JSON array, nothing else
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a world-class film critic. Always respond in valid JSON only. No markdown, no explanation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
    )

    if not response.choices:
        error_msg = getattr(response, 'msg', 'Unknown API Error')
        if hasattr(response, 'code'):
            error_msg += f" (Code: {response.code})"
        raise Exception(f"API Error: {error_msg}")

    raw = response.choices[0].message.content.strip()

    # Clean up if Groq wraps in markdown code blocks
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    movies = json.loads(raw)
    return movies


def format_star_rating(rating):
    """Converts numeric rating (e.g. 4.5) to star string (e.g. ★★★★½)"""
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    return "★" * full_stars + ("½" if half_star else "") + "☆" * empty_stars


def format_movies_output(movies, user_input):
    """
    Formats the list of movie dicts into a clean readable text output
    for display in the Gradio textbox.
    """
    lines = []
    lines.append(f"🎬 TOP 5 RECOMMENDATIONS FOR: \"{user_input.upper()}\"")
    lines.append("═" * 60)

    for i, movie in enumerate(movies, 1):
        stars = format_star_rating(movie['rating'])
        tags = "  ".join([f"#{tag}" for tag in movie.get('mood_tags', [])])

        lines.append(f"\n{'─' * 60}")
        lines.append(f"  #{i}  {movie['title']} ({movie['year']})")
        lines.append(f"{'─' * 60}")
        lines.append(f"  🎭 Genre     : {movie['genre']}")
        lines.append(f"  🎬 Director  : {movie['director']}")
        lines.append(f"  ⭐ Rating    : {stars}  ({movie['rating']}/5)")
        lines.append(f"  🏷️  Tags      : {tags}")
        lines.append(f"\n  ✅ WHY THIS MOVIE?")
        lines.append(f"     {movie['match_reason']}")
        lines.append(f"\n  📝 AI REVIEW")
        lines.append(f"     {movie['review']}")

    lines.append(f"\n{'═' * 60}")
    lines.append("  💡 Tip: Try another mood or movie for fresh recommendations!")
    lines.append(f"{'═' * 60}")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN BOT FUNCTION (called by Gradio)
# ──────────────────────────────────────────────────────────────────────────────

def movie_bot(user_input, input_type, genre_filter):
    """
    Main function connected to Gradio UI.
    Validates input → calls Groq → formats output.
    """

    # Input validation
    if not user_input or not user_input.strip():
        return "⚠️ Please enter a mood or a movie name to get recommendations!"

    user_input = user_input.strip()

    try:
        print(f"\n[INFO] Getting recommendations for: '{user_input}'")

        # Get recommendations from Groq
        movies = get_movie_recommendations(user_input, input_type, genre_filter)

        # Format nicely for display
        output = format_movies_output(movies, user_input)

        print("[OK] Recommendations ready!")
        return output

    except json.JSONDecodeError:
        return "❌ Error: AI returned unexpected format. Please try again!"

    except Exception as e:
        error = str(e)
        if "credits" in error.lower() or "403" in error:
            return "❌ Your Groq account has no credits or access."
        elif "401" in error or "Unauthorized" in error or "认证失败" in error:
            return "❌ Invalid API Key! Please check your GROQ_API_KEY in app.py"
        elif "rate" in error.lower():
            return "⏳ Rate limit hit. Please wait a moment and try again."
        else:
            return f"❌ Error: {error}"


# ──────────────────────────────────────────────────────────────────────────────
# GRADIO UI
# ──────────────────────────────────────────────────────────────────────────────

# Custom CSS for a cinematic dark theme
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500&display=swap');

body, .gradio-container {
    background: #0a0a0f !important;
    font-family: 'DM Sans', sans-serif !important;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
}

.gr-button-primary {
    background: linear-gradient(135deg, #e50914, #b20710) !important;
    border: none !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
}

.gr-button-primary:hover {
    background: linear-gradient(135deg, #ff1a1a, #cc0000) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(229,9,20,0.4) !important;
}

textarea, input {
    background: #1a1a2e !important;
    border: 1px solid #2a2a4a !important;
    color: #e8e8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

.gr-box {
    background: #12121f !important;
    border: 1px solid #1e1e3a !important;
}

label {
    color: #a0a0c0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}

select {
    background: #1a1a2e !important;
    color: #e8e8e8 !important;
    border: 1px solid #2a2a4a !important;
}

.gr-form {
    background: transparent !important;
}
"""

with gr.Blocks(
    title="🎬 CineBot — Movie Recommendation + Review"
) as app:

    # ── Header ────────────────────────────────────────────────────────────────
    gr.Markdown("""
    <div style="text-align:center; padding: 30px 0 10px 0;">
        <h1 style="font-size: 3em; color: #e50914; margin-bottom: 5px; letter-spacing: -1px;">
            🎬 CineBot
        </h1>
        <p style="color: #888; font-size: 1.1em; margin: 0;">
            Your AI-powered movie companion — recommendations + reviews in seconds
        </p>
        <p style="color: #555; font-size: 0.85em; margin-top: 8px;">
            Powered by <strong style="color:#f55036">Groq</strong>
        </p>
    </div>
    """)

    gr.Markdown("---")

    # ── Controls ──────────────────────────────────────────────────────────────
    with gr.Row():
        with gr.Column(scale=1):
            input_type = gr.Radio(
                choices=["🎭 I'm in a mood", "🎥 I liked a movie"],
                value="🎭 I'm in a mood",
                label="What are you basing this on?",
            )

        with gr.Column(scale=1):
            genre_filter = gr.Dropdown(
                choices=[
                    "Any Genre", "Action", "Comedy", "Drama", "Horror",
                    "Romance", "Sci-Fi", "Thriller", "Animation",
                    "Documentary", "Fantasy", "Mystery", "Crime"
                ],
                value="Any Genre",
                label="🎭 Genre Preference (optional)"
            )

    # ── Input + Button ────────────────────────────────────────────────────────
    with gr.Row():
        user_input = gr.Textbox(
            label="💬 Enter your mood or movie name",
            placeholder="e.g.  'feeling adventurous'  or  'Interstellar'  or  'sad and rainy day'",
            lines=1,
            scale=4
        )
        submit_btn = gr.Button("🎬 Get Recommendations", variant="primary", scale=1, size="lg")

    # ── Output ────────────────────────────────────────────────────────────────
    output_box = gr.Textbox(
        label="🍿 Your Personalised Movie Recommendations",
        lines=35,
        placeholder="Your movie recommendations will appear here..."
    )

    # ── Connect ───────────────────────────────────────────────────────────────
    submit_btn.click(
        fn=movie_bot,
        inputs=[user_input, input_type, genre_filter],
        outputs=output_box
    )

    user_input.submit(
        fn=movie_bot,
        inputs=[user_input, input_type, genre_filter],
        outputs=output_box
    )

    # ── Examples ──────────────────────────────────────────────────────────────
    gr.Markdown("### 💡 Quick Examples — Click to Try:")
    gr.Examples(
        examples=[
            ["feeling adventurous and excited", "🎭 I'm in a mood", "Action"],
            ["sad and want to cry", "🎭 I'm in a mood", "Drama"],
            ["happy and want to laugh", "🎭 I'm in a mood", "Comedy"],
            ["can't sleep, need something thrilling", "🎭 I'm in a mood", "Thriller"],
            ["Interstellar", "🎥 I liked a movie", "Sci-Fi"],
            ["The Dark Knight", "🎥 I liked a movie", "Any Genre"],
            ["3 Idiots", "🎥 I liked a movie", "Any Genre"],
            ["Inception", "🎥 I liked a movie", "Any Genre"],
        ],
        inputs=[user_input, input_type, genre_filter]
    )

    # ── Footer ────────────────────────────────────────────────────────────────
    gr.Markdown("""
    ---
    <div style="text-align:center; color:#555; font-size:0.85em; padding: 10px 0;">
        ⚡ Powered by <strong>Groq</strong> &nbsp;|&nbsp;
        🎬 CineBot — Movie Recommendation + Review Bot &nbsp;|&nbsp;
        Built with Gradio
    </div>
    """)


# ──────────────────────────────────────────────────────────────────────────────
# RUN THE APP
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n[INFO] CineBot is starting...")
    print("[INFO] Open your browser at: http://localhost:7860")
    print("[INFO] Press Ctrl+C to stop\n")
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        css=custom_css,
        theme=gr.themes.Base(
            primary_hue="red",
            secondary_hue="slate",
            neutral_hue="slate"
        )
    )
