![Tests](https://github.com/willynikes2/presient/actions/workflows/test.yml/badge.svg)

# Presient

**Presient** is a biometric presence authentication platform using mmWave radar and heartbeat signatures to recognize individual users in a smart home environment.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Dev Container](https://img.shields.io/badge/devcontainer-ready-blue)
![GitHub Repo stars](https://img.shields.io/github/stars/YOUR_USERNAME/presient?style=social)
[![Open in Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?template_repository=YOUR_USERNAME/presient)

---

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

## 🚀 Getting Started

### Local Development (Docker)

```bash
cp backend/.env.example backend/.env
docker-compose up --build
```

Visit:
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (admin@presient.io / admin)

### Browser (GitHub Codespaces)

Click the badge above to open the repo in your browser with full dev environment!

## 📄 License

This project is licensed under the MIT License.
