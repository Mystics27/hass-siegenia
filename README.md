# Siegenia Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/Mystics27/hass-siegenia)](https://github.com/Mystics27/hass-siegenia/releases)
[![GitHub license](https://img.shields.io/github/license/Mystics27/hass-siegenia)](https://github.com/Mystics27/hass-siegenia/blob/main/LICENSE)

Home Assistant Custom Integration für **Siegenia AEROPAC IE SMART** Wandlüfter und andere Siegenia Klimageräte.

Diese Integration ermöglicht die vollständige Steuerung von Siegenia-Geräten über Home Assistant via WebSocket-Verbindung.

## 🎯 Unterstützte Geräte

- **AEROPAC IE SMART** ✅ (getestet)
- AEROMAT VT 
- DRIVE axxent Family
- SENSOAIR
- AEROVITAL ambience
- MHS Family
- AEROTUBE
- Universal Module

*Basierend auf dem bewährten ioBroker Siegenia Adapter*

## ✨ Features

### 🌀 Lüftersteuerung
- **Ein/Aus-Steuerung** über Fan Entity
- **Direkte Stufenauswahl 0-7** über Number Entity (empfohlen)
- **Prozentuale Steuerung** 0-100% über Fan Entity
- **Echtzeit-Updates** über WebSocket

### 📊 Zusätzliche Informationen
- Aktuelle Lüfterstufe und Stufenname
- Gerätestatus (aktiv/inaktiv)
- Timer-Informationen (falls verfügbar)
- Warnungen und Fehlermeldungen
- Geräte-Informationen (Version, Seriennummer, etc.)

### 🔧 Services
- `siegenia.set_fan_level`: Direkte Stufeneinstellung (0-7)

## 📦 Installation

### Option 1: HACS (empfohlen)

1. Stellen Sie sicher, dass [HACS](https://hacs.xyz/) installiert ist
2. Gehen Sie zu HACS → Integrationen
3. Klicken Sie auf die drei Punkte (⋮) → Custom repositories
4. Fügen Sie hinzu: `https://github.com/Mystics27/hass-siegenia`
5. Kategorie: `Integration`
6. Installieren Sie "Siegenia"
7. **Starten Sie Home Assistant neu**

### Option 2: Manuelle Installation

1. Laden Sie die neueste Version von den [Releases](https://github.com/Mystics27/hass-siegenia/releases) herunter
2. Entpacken Sie die Dateien nach `custom_components/siegenia/`
3. **Starten Sie Home Assistant neu**

### Dateistruktur nach Installation
```
custom_components/siegenia/
├── translations/
    ├── de.json
    ├── en.json
├── __init__.py
├── config_flow.py
├── const.py
├── coordinator.py
├── device.py
├── fan.py
├── number.py
├── services.py
├── manifest.json
├── strings.json
└── services.yaml
```

## ⚙️ Konfiguration

### Integration hinzufügen

1. Gehen Sie zu **Einstellungen** → **Geräte & Services**
2. Klicken Sie **+ Integration hinzufügen**
3. Suchen Sie nach **"Siegenia"**
4. Geben Sie Ihre Gerätedaten ein:

| Feld | Beschreibung | Beispiel |
|------|-------------|----------|
| **IP-Adresse** | IP Ihres Siegenia Geräts | `192.168.1.123` |
| **Port** | WebSocket Port | `443` (Standard) |
| **Benutzername** | Login-Benutzername | `admin` |
| **Passwort** | Login-Passwort | `0000` |
| **SSL verwenden** | HTTPS/WSS aktivieren | ✅ (empfohlen) |

### Standardanmeldedaten
Falls Sie die Anmeldedaten nicht geändert haben, versuchen Sie:
- **Benutzername**: `admin` oder `user`
- **Passwort**: `0000`, `admin` oder Ihr WLAN-Passwort

## 🎮 Verwendung

### Entities

Nach erfolgreicher Einrichtung erhalten Sie folgende Entities:

#### 🌀 Fan Entity: `fan.aeropac_[name]`
- Ein/Aus-Buttons
- Prozentuale Geschwindigkeitsregelung (0-100%)
- Wird automatisch auf Stufen 0-7 gemappt

#### 🔢 Number Entity: `number.aeropac_[name]_lüfterstufe` ⭐️ **Empfohlen**
- **Direkter Stufen-Slider: 0-7**
- Stufe 0 = Aus
- Stufen 1-7 = Lüftergeschwindigkeit
- Viel benutzerfreundlicher!

### Dashboard-Karten

#### Einfache Steuerung
```yaml
type: entities
entities:
  - entity: number.aeropac_michael_lüfterstufe
    name: "Lüfterstufe"
  - type: divider
  - entity: fan.aeropac_michael
    attribute: fan_level_name
    name: "Aktuelle Stufe"
  - entity: fan.aeropac_michael
    attribute: device_active
    name: "Gerät aktiv"
```

#### Erweiterte Karte
```yaml
type: custom:mushroom-entity-card
entity: number.aeropac_michael_lüfterstufe
name: Wandlüfter
icon: mdi:fan
tap_action:
  action: more-info
```

## 🤖 Automationen

### Lüfter bei hoher Luftfeuchtigkeit
```yaml
automation:
  - alias: "Lüfter bei hoher Luftfeuchtigkeit"
    trigger:
      - platform: numeric_state
        entity_id: sensor.humidity_bathroom
        above: 70
    action:
      - service: number.set_value
        target:
          entity_id: number.aeropac_michael_lüfterstufe
        data:
          value: 4  # Stufe 4
```

### Nachtmodus (leise Stufe)
```yaml
automation:
  - alias: "Lüfter Nachtmodus"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: number.set_value
        target:
          entity_id: number.aeropac_michael_lüfterstufe
        data:
          value: 1  # Leise Stufe 1
```

### Lüfter ausschalten bei geschlossenem Fenster
```yaml
automation:
  - alias: "Lüfter aus bei geschlossenem Fenster"
    trigger:
      - platform: state
        entity_id: binary_sensor.window_bathroom
        to: "off"
        for: "00:05:00"  # 5 Minuten geschlossen
    action:
      - service: number.set_value
        target:
          entity_id: number.aeropac_michael_lüfterstufe
        data:
          value: 0  # Ausschalten
```

### Adaptive Lüftung basierend auf CO2
```yaml
automation:
  - alias: "Adaptive Lüftung CO2"
    trigger:
      - platform: numeric_state
        entity_id: sensor.co2_level
    action:
      - choose:
          - conditions:
              - condition: numeric_state
                entity_id: sensor.co2_level
                below: 600
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.aeropac_michael_lüfterstufe
                data:
                  value: 1
          - conditions:
              - condition: numeric_state
                entity_id: sensor.co2_level
                above: 800
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.aeropac_michael_lüfterstufe
                data:
                  value: 5
        default:
          - service: number.set_value
            target:
              entity_id: number.aeropac_michael_lüfterstufe
            data:
              value: 3
```

## 🔧 Services

### `siegenia.set_fan_level`
Direkte Lüfterstufe setzen (0-7):

```yaml
service: siegenia.set_fan_level
target:
  entity_id: fan.aeropac_michael
data:
  level: 3
```

## 🐛 Troubleshooting

### Debug-Logging aktivieren
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.siegenia: debug
```

### Häufige Probleme

#### ❌ "Failed to login to device"
**Lösungen:**
- IP-Adresse überprüfen: `ping 192.168.1.88`
- Standard-Anmeldedaten testen:
  - `admin` / `0000`
  - `user` / `0000` 
  - `admin` / `admin`
- Port ändern: `80` oder `8080` versuchen
- SSL deaktivieren für Test

#### ❌ "Cannot connect to device"
**Lösungen:**
- Netzwerk-Konnektivität prüfen
- Firewall-Einstellungen überprüfen
- Gerät neustarten
- Anderen Port versuchen

#### ❌ "Entity erscheint nicht"
**Lösungen:**
- Home Assistant Logs überprüfen
- Integration entfernen und neu hinzufügen
- `custom_components/siegenia/` Ordner-Berechtigung prüfen

### Test-Verbindung
Verwenden Sie das bereitgestellte Test-Script um die Verbindung zu testen:
```bash
cd /config
python3 test_connection.py
```

### Erweiterte Diagnostik
```bash
# WebSocket-Verbindung mit wscat testen (falls installiert)
wscat -c wss://192.168.1.123:443/WebSocket --no-check
```

## 📋 Technische Details

### Unterstützte Lüfterstufen (AEROPAC)
| Stufe | Beschreibung |
|-------|-------------|
| 0 | Aus |
| 1 | Stufe 1 (sehr leise) |
| 2 | Stufe 2 |
| 3 | Stufe 3 |
| 4 | Stufe 4 |
| 5 | Stufe 5 |
| 6 | Stufe 6 |
| 7 | Stufe 7 (maximum) |

### WebSocket-Kommunikation
- **Protokoll**: WSS (HTTPS WebSocket) oder WS
- **Port**: 443 (SSL) oder 80/8080 (unverschlüsselt)
- **Authentifizierung**: Benutzername/Passwort
- **Updates**: Real-time via WebSocket-Callbacks

## 🚀 Erweiterungsideen

Diese Integration kann in Zukunft erweitert werden für:

- [ ] **Timer-Steuerung** (Timer setzen/stoppen)
- [ ] **Sensor-Entities** (Temperatur, Luftfeuchtigkeit, CO2)
- [ ] **Beleuchtungssteuerung** (für AEROVITAL Modelle)
- [ ] **Erweiterte Gerätetypen** (AEROTUBE, MHS Family, etc.)
- [ ] **Wartungshinweise** (Filterwechsel-Erinnerungen)

## 💡 Beitragen

Beiträge sind willkommen! Bitte:

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Erstellen Sie einen Pull Request

### Entwicklung
```bash
# Repository klonen
git clone https://github.com/Mystics27/hass-siegenia.git
cd hass-siegenia

# Entwicklungsumgebung
pip install -r requirements_dev.txt
```

## 📝 Changelog

### v1.0.0
- ✅ Initiale Version
- ✅ Fan Entity mit Ein/Aus und Geschwindigkeitssteuerung
- ✅ Number Entity für direkte Stufenauswahl (0-7)
- ✅ WebSocket-Kommunikation
- ✅ Real-time Updates
- ✅ Konfiguration über UI

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.

## 🏆 Credits

- Basierend auf dem [ioBroker Siegenia Adapter](https://github.com/Apollon77/ioBroker.siegenia) von Apollon77
- WebSocket-Implementierung portiert von Node.js zu Python
- Home Assistant Integration erstellt mit ❤️

## 💬 Support

Bei Problemen oder Fragen:

1. **Schauen Sie in die [Issues](https://github.com/Mystics27/hass-siegenia/issues)**
2. **Erstellen Sie ein neues Issue** mit:
   - Home Assistant Version
   - Siegenia Gerätemodell und Firmware
   - Debug-Logs (siehe Troubleshooting)
   - Detaillierte Fehlerbeschreibung

---

**⭐ Gefällt Ihnen diese Integration? Geben Sie diesem Repository einen Stern!**
