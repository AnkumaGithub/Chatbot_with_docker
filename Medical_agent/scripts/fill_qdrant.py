import csv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import uuid
import argparse
import logging
import os
import chardet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def main(csv_path, qdrant_url, collection_name):
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False

    encoding = detect_encoding(csv_path)
    logger.info(f"Detected encoding: {encoding}")

    client = QdrantClient(qdrant_url, check_compatibility=False)
    encoder = SentenceTransformer("all-MiniLM-L6-v2")

    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            )
        )
        logger.info(f"Collection {collection_name} recreated")
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        return False

    points = []
    try:
        with open(csv_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)

            required_columns = ['Name', 'Symptoms']
            missing_columns = [col for col in required_columns if col not in reader.fieldnames]

            if missing_columns:
                logger.error(f"Missing required columns: {', '.join(missing_columns)}")
                return False

            logger.info(f"CSV headers: {reader.fieldnames}")

            for i, row in enumerate(reader):
                text = f"{row['Name']} {row['Symptoms']}"

                embedding = encoder.encode(text).tolist()

                payload = {
                    "name": row['Name'],
                    "symptoms": [s.strip() for s in row['Symptoms'].split(",")],
                }

                for field in ['Code', 'Treatments', 'Description']:
                    if field in row and row[field]:
                        if field == 'Treatments':
                            payload[field.lower()] = [t.strip() for t in row[field].split(",")]
                        else:
                            payload[field.lower()] = row[field]

                points.append(models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=payload
                ))

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1} rows")

    except UnicodeDecodeError as e:
        logger.error(f"Encoding error: {str(e)}. Try different encoding.")
        return False
    except Exception as e:
        logger.error(f"Error reading CSV: {str(e)}")
        return False

    try:
        if points:
            client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True
            )
            logger.info(f"Inserted {len(points)} diseases into Qdrant")
            return True
        else:
            logger.warning("No points to insert")
            return False
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Load medical data into Qdrant')
    parser.add_argument('--csv', type=str, required=True, help='Diseases_Symptoms_ru.csv')
    parser.add_argument('--qdrant', type=str, default='http://localhost:6333', help='Qdrant URL')
    parser.add_argument('--collection', type=str, default='diseases', help='Collection name')

    args = parser.parse_args()

    try:
        logger.info(f"Starting data loading from {args.csv}")
        success = main(args.csv, args.qdrant, args.collection)
        if success:
            logger.info("Data loading completed successfully")
            exit(0)
        else:
            logger.error("Data loading failed")
            exit(1)
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        exit(1)