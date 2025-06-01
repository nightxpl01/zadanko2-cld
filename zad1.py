from flask import Flask, request
import datetime
import requests
import os

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8069))
AUTHOR = "Michał Małysz"

print(f"Czas: {datetime.datetime.now()}")
print(f"Autor: {AUTHOR}")
print(f"Port: {PORT}")


LOCATIONS = {
    "Polska": ["Warszawa", "Kraków"]
}

API_KEY = "26b964c3980c2aa90c78114181364841"

@app.route("/")
def home():
    return """
        <h2>Wybierz lokalizację:</h2>
        <form action="/pogoda" method="get">
            <label>Kraj:</label>
            <select name="kraj">
                <option value="Polska">Polska</option>
            </select><br><br>
            <label>Miasto:</label>
            <select name="miasto">
                <option value="Warszawa">Warszawa</option>
                <option value="Kraków">Kraków</option>
            </select><br><br>
            <button type="submit">Pokaż pogodę</button>
        </form>
    """

@app.route("/pogoda")
def pogoda():
    city = request.args.get("miasto")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=pl"
    response = requests.get(url).json()

    temp = response["main"]["temp"]
    desc = response["weather"][0]["description"]

    return f"<h2>Pogoda w {city}:</h2><p>Temperatura: {temp}°C<br>Opis: {desc}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8069)
