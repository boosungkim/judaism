from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import requests
from dateutil.parser import parse as parse_datetime

app = Flask(__name__, template_folder='templates')

coords = {
    'New York': {'lat': 40.7128, 'lon': -74.0060},
    'Philadelphia': {'lat': 39.9526, 'lon': -75.1652},
    'Jerusalem': {'lat': 31.7683, 'lon': 35.2137},
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calendar')
def get_calendar():
    location = request.args.get('location', 'New York')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    if location not in coords:
        return jsonify({'error': 'Unsupported location'}), 400

    lat, lon = coords[location]['lat'], coords[location]['lon']

    # Hebcal API
    hebcal_url = f"https://www.hebcal.com/shabbat/?cfg=json&latitude={lat}&longitude={lon}&m=50"
    hebcal_data = requests.get(hebcal_url).json()

    # Sunrise-Sunset API (UTC)
    sun_api_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date_str}&formatted=0"
    sun_data = requests.get(sun_api_url).json().get('results', {})

    def parse_time(iso):
        try:
            return parse_datetime(iso) if iso else None
        except ValueError:
            return None


    sunrise = parse_time(sun_data.get('sunrise'))
    sunset = parse_time(sun_data.get('sunset'))
    chatzot = None
    mincha_gedola = None

    if sunrise and sunset:
        chatzot = sunrise + (sunset - sunrise) / 2
        halachic_hour = (sunset - sunrise) / 12
        mincha_gedola = chatzot + (halachic_hour / 2)

    # Parashah summary (basic examples)
    summaries = {
        'Emor': 'Discusses priestly duties, sacred times, and festivals.',
        'Achrei Mot': 'Covers Yom Kippur rituals and moral laws.',
        'Kedoshim': 'Outlines ethical mandates and holiness codes.',
        'Behar': 'Laws of Sabbatical and Jubilee years.'
    }

    parashah_item = next((i for i in hebcal_data.get('items', []) if i.get('category') == 'parashat'), None)
    parashah = parashah_item.get('title') if parashah_item else None
    parashah_summary = summaries.get(parashah.split()[-1], '') if parashah else ''

    response = {
        'location': location,
        'date': date_str,
        'hebrew_date': hebcal_data.get('date', 'N/A'),
        'items': hebcal_data.get('items', []),
        'zmanim': {
            'sunrise': sunrise.strftime('%H:%M') if sunrise else None,
            'sunset': sunset.strftime('%H:%M') if sunset else None,
            'chatzot': chatzot.strftime('%H:%M') if chatzot else None,
            'mincha_gedola': mincha_gedola.strftime('%H:%M') if mincha_gedola else None
        },
        'parashah_summary': parashah_summary
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
