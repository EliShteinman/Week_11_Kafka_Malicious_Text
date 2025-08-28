from shared.text_processing import TextProcessing
from shared.kafka_utils import AsyncKafkaProducer


class PreprocessorService:
    def __init__(self):
        self.cleaner = TextProcessing()
        self.producer = AsyncKafkaProducer(bootstrap_servers='localhost:9092')

    async def process_text(self,topic:str, message: dict) -> dict:
        d= message
        text = d.get("text", "")

        d['b'] = self.cleaner.clean_central(text)
        t = 'g' if topic == 'y' else 'b'

        f = await self.producer.send_json(t, d)
        return f




if __name__ == "__main__":
    examples = [
        "This is   a SAMPLE text, with Punctuation!!",
        "NLTK is a great library for text processing.",
        "Cleaning   TEXT??? is sometimes  tricky...",
        "Stopwords should be removed in this sentence.",
        "Running, runner, runs – all should be stemmed.",
    ]

    for text in examples:
        cleaned = TextProcessing.clean_central(text)
        print(f"Original: {text}")
        print(f"Cleaned : {cleaned}")
        print("-" * 50)
