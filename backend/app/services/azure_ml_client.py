import requests
from app.config.config import settings
from app.utils.logger import logger


class AzureMLClient:
    def __init__(self):
        self.endpoint = settings.AZURE_ML_ENDPOINT
        self.api_key = settings.AZURE_ML_API_KEY

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def predict(self, features: dict) -> float:
        if not self.is_configured():
            raise RuntimeError("Azure ML client is not configured")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"data": features}
        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            # Accept {"result": 123.45} or {"prediction": 123.45} or plain number
            if isinstance(result, (int, float)):
                return float(result)
            for key in ("result", "prediction", "price", "output"):
                if key in result:
                    return float(result[key])
            raise RuntimeError(f"Unexpected Azure ML response format: {result}")
        except requests.HTTPError as e:
            logger.error(f"Azure ML HTTP error: {e}")
            raise RuntimeError(f"Azure ML HTTP error: {e}") from e
        except requests.Timeout:
            logger.error("Azure ML request timed out")
            raise RuntimeError("Azure ML request timed out")
        except Exception as e:
            logger.error(f"Azure ML prediction failed: {e}")
            raise RuntimeError(f"Azure ML prediction failed: {e}") from e
