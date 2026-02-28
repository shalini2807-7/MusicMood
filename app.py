from flask import Flask, render_template, request
import google.generativeai as genai
import requests
import os
from creds import GEMINI_API_KEY,YOUTUBE_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)


# 🔑 YouTube API key    



def get_song_suggestions(image_path, language):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    Analyze this image and suggest 5 songs in {language}.
    The songs should match the mood, environment, or feeling of the image.

    Return ONLY in this format:
    Song Name - Artist
    Song Name - Artist
    Song Name - Artist
    Song Name - Artist
    Song Name - Artist

    Do not add explanations.
    """

    with open(image_path, "rb") as img:
        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": img.read()}]
        )

    text = response.text.strip().split("\n")
    print(text)

    # clean results
    songs = [line.strip() for line in text if "-" in line]

    return songs

def search_youtube(song_query):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={song_query}&key={YOUTUBE_API_KEY}&type=video&maxResults=1"

    response = requests.get(url).json()

    if response.get("items"):
        item = response["items"][0]
        return {
            "title": item["snippet"]["title"],
            "videoId": item["id"]["videoId"]
        }
    return None




def fetch_songs(mood, language):
    query = f"{mood} {language} songs"

    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&type=video&maxResults=6"

    response = requests.get(url).json()

    songs = []
    for item in response.get("items", []):
        songs.append({
            "title": item["snippet"]["title"],
            "videoId": item["id"]["videoId"]
        })

    return songs


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/recommend", methods=["POST"])
def recommend():
    image = request.files["image"]
    language = request.form["language"]

    if not os.path.exists("static/uploads"):
        os.makedirs("static/uploads")

    image_path = "static/uploads/upload.jpg"
    image.save(image_path)

    # ✅ Ask Gemini for songs
    suggested_songs = get_song_suggestions(image_path, language)
    print(suggested_songs)

    # ✅ Search each on YouTube
    results = []
    for song in suggested_songs:
        yt = search_youtube(song)
        if yt:
            results.append(yt)

    return render_template("result.html", songs=results)


if __name__ == "__main__":
    app.run(debug=True)