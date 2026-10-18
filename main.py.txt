import os
import asyncio
from fastapi import FastAPI
from hilo import HiloClient

app = FastAPI(title="Passerelle Hilo pour ESP01")

# Récupération des identifiants sécurisés via les variables d'environnement du Cloud
HILO_USERNAME = os.getenv("HILO_USERNAME")
HILO_PASSWORD = os.getenv("HILO_PASSWORD")

@app.get("/status")
async def get_hilo_status():
    """
    Retourne l'état actuel sous forme de texte brut pour l'ESP01:
    0 = Normal, 1 = Préchauffage, 2 = Réduction (Pointe)
    """
    if not HILO_USERNAME or not HILO_PASSWORD:
        return "0"  # Sécurité : si non configuré, mode normal.

    try:
        # Connexion asynchrone à l'API Hilo
        async with HiloClient(HILO_USERNAME, HILO_PASSWORD) as client:
            await client.authenticate()
            
            # Récupération des données du compte et des défis
            locations = await client.get_locations()
            if not locations:
                return "0"
            
            # On prend la première résidence du compte
            location = locations[0]
            await location.update()
            
            # Vérification des défis de pointe actifs
            current_event = location.current_event
            
            if current_event:
                # L'événement existe, on vérifie sa phase actuelle
                phase = current_event.phase.lower()
                if "preheat" in phase or "préchauffage" in phase:
                    return "1"
                elif "reduction" in phase or "réduction" in phase:
                    return "2"
            
            return "0" # Aucun événement ou phase de reprise/inconnue
            
    except Exception as e:
        # En cas d'erreur de connexion à Hilo, on retourne 0 pour ne pas bloquer le chauffage par erreur
        print(f"Erreur Hilo: {e}")
        return "0"

if __name__ == "__main__":
    import uvicorn
    # Lancement local (Utile pour vos tests)
    uvicorn.run(app, host="0.0.0.0", port=8000)
