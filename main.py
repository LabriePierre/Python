import os
import sys
from types import ModuleType

# --- ASTUCE DE SIMULATION (MOCK) POUR HOME ASSISTANT ---
# On crée un faux module 'homeassistant' pour que pyhilo ne plante pas au démarrage
if "homeassistant" not in sys.modules:
    mock_ha = ModuleType("homeassistant")
    mock_ha.helpers = ModuleType("helpers")
    mock_ha.helpers.config_entry_oauth2_flow = ModuleType("config_entry_oauth2_flow")
    
    # On ajoute la classe vide dont pyhilo a besoin pour compiler
    class OAuth2Session:
        def __init__(self, *args, **kwargs): pass

    mock_ha.helpers.config_entry_oauth2_flow.OAuth2Session = OAuth2Session
    sys.modules["homeassistant"] = mock_ha
    sys.modules["homeassistant.helpers"] = mock_ha.helpers
    sys.modules["homeassistant.helpers.config_entry_oauth2_flow"] = mock_ha.helpers.config_entry_oauth2_flow
# ------------------------------------------------------

import asyncio
from fastapi import FastAPI
from pyhilo import HiloClient

app = FastAPI(title="Passerelle Hilo pour ESP01")

HILO_USERNAME = os.getenv("HILO_USERNAME")
HILO_PASSWORD = os.getenv("HILO_PASSWORD")

@app.get("/status")
async def get_hilo_status():
    if not HILO_USERNAME or not HILO_PASSWORD:
        return "0"

    try:
        async with HiloClient(HILO_USERNAME, HILO_PASSWORD) as client:
            await client.authenticate()
            
            locations = await client.get_locations()
            if not locations:
                return "0"
            
            # Sélection de la première résidence
            location = locations[0] if isinstance(locations, list) else locations
            await location.update()
            
            # Récupération de l'événement en cours
            current_event = location.current_event
            
            if current_event:
                phase = current_event.phase.lower()
                if "preheat" in phase or "préchauffage" in phase:
                    return "1"
                elif "reduction" in phase or "réduction" in phase:
                    return "2"
            
            return "0"
            
    except Exception as e:
        print(f"Erreur Hilo: {e}")
        return "0"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
