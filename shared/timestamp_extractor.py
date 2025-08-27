import re

class Time_extractor:
    def __init__(self):
        # Different types of date regexes to extract below types of formats
        self.DateTimeRegex = {
            'day-month-year': r'\b\d{4}-\d{2}-\d{2}\b'
        }
        # Consolidated regex with many possible timestamps
        self.reg = '|'.join(self.DateTimeRegex.values())

    ## Function to remove some special characters
    def preprocess(self, x):
        x = x.replace('\t', ' ')
        x = x.replace('\n', ' ')
        x = x.replace('(', ' ')
        x = x.replace(')', ' ')
        x = x.replace('[', ' ')
        x = x.replace(']', ' ')
        x = x.replace('{', ' ')
        x = x.replace('}', ' ')
        x = x.replace(',', ' ')
        x = x.replace('"', '')
        x = x.replace("'", '')
        return (x)

    ## Function to extract date and time
    def DateTimeExtractor(self, x):
        x = self.preprocess(x)
        DT = re.findall(self.reg, x)
        return (DT)

if __name__ == '__main__':
    time_extractor = Time_extractor()
    samplestring1 = 'scala> val xorder= new order(1,"kf hkdg hj h 2025-02-22 hug gf")'
    print(time_extractor.DateTimeExtractor(samplestring1))