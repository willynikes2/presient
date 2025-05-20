# Presient

**Presient** is a biometric presence authentication platform that uses mmWave radar and heartbeat signatures to recognize individual users in a smart home environment. Unlike traditional motion detectors, Presient knows *who* is home.

## 🌟 Features

- Identity-based presence detection using radar + heartbeat biometrics
- BLE/Wi-Fi sensor registration and management via mobile app
- Local and cloud profile matching support
- MQTT, Home Assistant, and Matter integration
- OTA firmware updates via mobile app
- Privacy-first: supports offline mode and local-only operation
- Developer-ready: open API, custom automations, CLI tools

## 🔧 Tech Stack

| Layer        | Stack                                   |
|--------------|------------------------------------------|
| Frontend     | React Native (Expo)                     |
| Backend      | FastAPI + Supabase                      |
| Sensor       | ESP32 + mmWave radar + UART             |
| Firmware     | ESPHome/Arduino OTA                     |
| Integrations | MQTT, Webhooks, HealthKit/Fitbit APIs   |

## 🧱 Folder Structure

```bash
presient/
├── frontend/                # React Native app
├── backend/                 # FastAPI server
├── firmware/                # ESP32 firmware
├── docs/                    # Specs, planning, diagrams
└── README.md
```

## 🚀 Getting Started

1. Clone the repo:
```bash
git clone https://github.com/YOUR_USERNAME/presient.git
```

2. Set up the mobile app:
```bash
cd frontend && npm install && expo start
```

3. Start the backend (local):
```bash
cd backend && uvicorn main:app --reload
```

4. Flash the firmware to your mmWave sensor and test pairing.

## 🤝 Contributing

We’re building for open smart homes. If you're a developer, engineer, or researcher and want to contribute, reach out or submit a PR.

## 📄 License

MIT License
