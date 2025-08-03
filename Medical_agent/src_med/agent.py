import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MedicalAgent:
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant-service:6333")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.collection_name = os.getenv("COLLECTION_NAME", "diseases")
        self.initialize_clients()
        logger.info("MedicalAgent initialized")

    def initialize_clients(self):
        try:
            self.qdrant = QdrantClient(self.qdrant_url)
            self.encoder = SentenceTransformer(self.embedding_model)
            logger.info("Clients initialized successfully")

            # Проверка соединения с Qdrant
            collections = self.qdrant.get_collections()
            logger.info(f"Available collections: {[c.name for c in collections.collections]}")
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            raise

    def search_diseases(self, symptoms: List[str]) -> List[Dict]:
        if not symptoms:
            return []

        try:
            symptoms_text = " ".join(symptoms)
            embedding = self.encoder.encode(symptoms_text).tolist()

            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=3,
                with_payload=True
            )

            diseases = []
            for result in results:
                disease = {
                    "id": result.id,
                    "name": result.payload["name"],
                    "score": result.score,
                    "symptoms": result.payload["symptoms"],
                    "treatments": result.payload.get("treatments", [])
                }
                diseases.append(disease)

            logger.info(f"Found {len(diseases)} diseases for symptoms: {symptoms}")
            return diseases
        except Exception as e:
            logger.error(f"Error searching diseases: {str(e)}")
            return []

    def generate_question(self, top_disease: Dict, confirmed_symptoms: List[str]) -> str:
        if not top_disease:
            return "Опишите ваши симптомы подробнее?"

        missing_symptoms = [s for s in top_disease["symptoms"] if s not in confirmed_symptoms]

        if missing_symptoms:
            return f"Есть ли у вас {', '.join(missing_symptoms[:2])}?"
        else:
            return "Какие еще симптомы вы испытываете?"

    def make_diagnosis(self, top_disease: Dict, confirmed_symptoms: List[str]) -> str:
        if not top_disease:
            return "Не удалось определить заболевание по описанным симптомам"

        return (
            f"Предварительный диагноз: {top_disease['name']}\n"
            f"Лечение: {top_disease['treatments']}\n"
            f"Совпадающие симптомы: {', '.join(confirmed_symptoms)}"
        )