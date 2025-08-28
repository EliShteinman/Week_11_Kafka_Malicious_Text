import os

import cleantext
import nltk

NLTK_DIR = os.path.join(os.getcwd(), "nltk_data")
nltk.data.path.append(NLTK_DIR)
nltk.download("stopwords", download_dir=NLTK_DIR, quiet=True)


class TextProcessing:
    def __init__(self, path_download: str = None):
        NLTK_DIR = os.path.join(os.getcwd(), "nltk_data")
        nltk.data.path.append(NLTK_DIR)
        nltk.download("stopwords", download_dir=NLTK_DIR, quiet=True)

    @staticmethod
    def clean_central(text):
        if not text or text.isspace():
            return ""
        return cleantext.clean(
            text,
            lowercase=True,
            extra_spaces=True,
            punct=True,
            stopwords=True,
            stemming=True,
            reg=r"[^\w\s]",
            reg_replace=" ",
        )


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

    texts = [
        "Running, runner, runs – all should be stemmed.",
        "An em—dash should not break tokenization — ideally.",
        "Smart quotes “like these” and ellipses… should normalize.",
        "URLs like https://example.com and emails a@b.com should be handled.",
    ]
    for t in texts:
        cleaned = TextProcessing.clean_central(t)
        print("Original:", t)
        print("Cleaned :", cleaned)
        print("-" * 50)
