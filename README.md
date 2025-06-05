# 🎪 Gestione Palchi

> Sistema completo per la gestione dei palchi comunali organizzati dalle associazioni Pro Loco

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python)](https://python.org)
[![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)

## ✨ Caratteristiche

- 🎯 **Gestione Eventi** - Pianificazione e monitoraggio completo degli eventi
- 👥 **Associazioni & Volontari** - Registro delle Pro Loco e dei volontari certificati
- 📊 **Dashboard & Report** - Analisi dettagliate e reportistica avanzata
- 🔐 **Autenticazione** - Sistema di login sicuro con JWT
- 🚀 **Performance** - API ottimizzate con middleware per compressione e caching
- 🐳 **Docker Ready** - Deployment semplificato con Docker Compose
- 📱 **Frontend Integrato** - Interfaccia web responsive

## 🏗️ Architettura

```
gestione-palchi/
├── 🎯 app/
│   ├── core/           # Configurazione e autenticazione
│   ├── models/         # Modelli SQLAlchemy
│   ├── routers/        # Endpoint API REST
│   ├── schemas/        # Validazione Pydantic
│   └── services/       # Logica di business
├── 🌐 public/          # Frontend statico
├── 📄 data/            # Database SQLite
└── 🐳 Docker files
```

## 🚀 Quick Start

### Con Docker (Consigliato)

```bash
# Clone del repository
git clone https://github.com/username/gestione-palchi.git
cd gestione-palchi

# Avvio con Docker Compose
docker-compose up -d

# L'applicazione sarà disponibile su http://localhost:8000
```

### Installazione Locale

```bash
# Installazione dipendenze
pip install -r requirements.txt

# Avvio del server
python run.py
```

## 🎯 Endpoints Principali

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/` | GET | Frontend principale |
| `/health` | GET | Health check |
| `/docs` | GET | Documentazione API |
| `/api/v1/auth/*` | POST | Autenticazione |
| `/api/v1/events/*` | CRUD | Gestione eventi |
| `/api/v1/associations/*` | CRUD | Gestione associazioni |
| `/api/v1/reports/*` | GET | Report e statistiche |

## 📊 Modelli Dati

### 🎪 Event
- Titolo, data/ora inizio e fine
- Ubicazione e dimensioni palco
- Stato evento (5 fasi dal planning al completamento)
- Richiedente e date assemblee

### 👥 Association
- Nome associazione Pro Loco
- Persona di contatto e sede
- Codice fiscale
- Volontari associati

### 🙋 Volunteer
- Dati anagrafici completi
- Certificazione e associazione di appartenenza

## 🔧 Configurazione

Le variabili d'ambiente principali:

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/gestione_palchi.db
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:8000
```

## 🧪 Testing

```bash
# Esecuzione test
pytest

# Con coverage
pytest --cov=app
```

## 🚀 Performance

- **Middleware GZip** per compressione automatica
- **Header timing** per monitoraggio performance
- **Logging avanzato** per richieste lente (>1s)
- **CORS ottimizzato** con cache 24h
- **Health check** per monitoring

## 🐳 Docker Services

- **gestione-palchi**: Applicazione principale Python/FastAPI
- **redis**: Cache e sessioni
- **Volumes**: Persistenza dati e logs

## 🤝 Contribuire

1. Fork del progetto
2. Feature branch (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Pull Request

## 📄 License

Questo progetto è distribuito sotto licenza MIT. Vedi `LICENSE` per dettagli.

---

<div align="center">

**🎪 Gestione Palchi** - *Semplificare la gestione degli eventi Pro Loco*

*Made with ❤️ in Italy*

</div>