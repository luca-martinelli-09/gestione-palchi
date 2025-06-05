#!/usr/bin/env python3
import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    print("🚀 Avvio del server Gestione Palchi API...")
    print(f"   🔧 Modalità debug: {settings.debug}")
    print(f"   📊 Livello log: {settings.log_level}")
    print(f"   🔗 Prefisso API: {settings.api_prefix}")
    print(f"   🌐 Server: http://localhost:{settings.app_port}")
    print(f"   📚 Documentazione: http://localhost:{settings.app_port}/docs")
    print("")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=settings.debug,
        workers=1 if settings.debug else 4,
    )
