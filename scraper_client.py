import time
import requests
import io
import pandas as pd
from config import SCRAPER_API_URL

class ScraperClient:
    def __init__(self, base_url: str = SCRAPER_API_URL):
        self.base_url = base_url

    def criar_job(self, queries: list) -> str:
        url = f"{self.base_url}/api/v1/jobs"
        payload = {
            "name": f"BDR - {time.strftime('%Y-%m-%d')}",
            "keywords": queries,
            "depth": 3,
            "email": True,
            "lang": "pt",
            "max_time": 3600
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("id")

    def checar_status(self, job_id: str) -> str:
        url = f"{self.base_url}/api/v1/jobs/{job_id}"
        response = requests.get(url)
        response.raise_for_status()
        # Ajustar de acordo com o retorno exato da sua API de scraping
        return response.json().get("Status") or response.json().get("status")

    def baixar_csv(self, job_id: str) -> pd.DataFrame:
        url = f"{self.base_url}/api/v1/jobs/{job_id}/download"
        response = requests.get(url)
        response.raise_for_status()
        
        # Converte os bytes recebidos diretamente para um DataFrame do Pandas
        csv_data = io.BytesIO(response.content)
        return pd.read_csv(csv_data)
