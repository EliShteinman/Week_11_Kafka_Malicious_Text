import re


class TimeExtractor:
    def __init__(self):
        # Different types of date regexes to extract below types of formats
        self.DateTimeRegex = {
            "year-month-day-dash": r"\b\d{4}-\d{2}-\d{2}\b",
            "day-month-year-dash": r"\b\d{2}-\d{2}-\d{4}\b",
            "year-month-day-slash": r"\b\d{4}/\d{2}/\d{2}\b",
            "day-month-year-slash": r"\b\d{2}/\d{2}/\d{4}\b"
        }
        # Consolidated regex with many possible timestamps
        self.reg = "|".join(self.DateTimeRegex.values())

    # Function to remove some special characters
    def preprocess(self, x):
        x = x.replace("\t", " ")
        x = x.replace("\n", " ")
        x = x.replace("(", " ")
        x = x.replace(")", " ")
        x = x.replace("[", " ")
        x = x.replace("]", " ")
        x = x.replace("{", " ")
        x = x.replace("}", " ")
        x = x.replace(",", " ")
        x = x.replace('"', "")
        x = x.replace("'", "")
        return x

    # Function to extract date and time
    def date_time_extractor(self, x):

        x = self.preprocess(x)
        dt = re.findall(self.reg, x)
        return dt


if __name__ == "__main__":
    time_extractor = TimeExtractor()
    samplestring1 = 'scala> val xorder= new order(1,"kf hkdg hj h 2025-02-22 hug gf")'
    print(time_extractor.date_time_extractor(samplestring1))
