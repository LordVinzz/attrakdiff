import sys
import pandas as pd
import matplotlib.pyplot as plt
import uuid
import csv
import os

class Settings:
    def __init__(self, path):

        self.config = {}

        with open(path, 'r') as f:

            for line in f:

                line = line.strip()
                if line and '=' in line:
                    k, v = line.split('=', 1)
                    self.config[k.strip()] = v.strip()

    def get(self, key, default=None):
        return self.config.get(key, default)

class SheetProcessor:
    def __init__(self):

        self.settings = Settings('settings.properties')
        self.sheet_folder = self.settings.get('SHEET_FOLDER', './sheets')
        
        if len(sys.argv) > 1:
            self.sheet_folder = sys.argv[1]

        try:
            self.scale_factor = eval(float(self.settings.get('SCALE_FACTOR', '10/21')))
            self.bias = float(self.settings.get('BIAS', '10'))
        except ValueError:
            self.scale_factor = 10/21
            self.bias = 10
            
        self.output = self.settings.get('OUTPUT', 'results.csv')
        self.global_vars = {"qhs": 0, "qp": 0, "qhi": 0, "att": 0}
        self.score_columns = ['-3', '-2', '-1', '0', '1', '2', '3']

    def compute_score(self, row):
        for col in self.score_columns:
            if pd.notna(row[col]) and str(row[col]).strip().lower() == 'x':
                return int(col)
        return 0

    def process(self, filename):
        file_path = os.path.join(self.sheet_folder, filename)
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            var = row['id']
            sign = 1
            if var[0] == '-':
                sign = int(f'{var[0]}1')
                var = var[1:]
            self.global_vars[var] += sign * self.compute_score(row)
        self.scaled_values = {k: round(v * self.scale_factor + self.bias, 2) for k, v in self.global_vars.items()}

    def append_to_csv(self):
        cols = ["UUID", "avg_qhs", "avg_qp", "avg_qhi", "avg_att", "qh_pt"]
        data = {
            "UUID": str(uuid.uuid1()),
            "avg_qhs": self.scaled_values["qhs"],
            "avg_qp": self.scaled_values["qp"],
            "avg_qhi": self.scaled_values["qhi"],
            "avg_att": self.scaled_values["att"],
            "qh_pt": f"({self.scaled_values['qp']},{(self.scaled_values['qhs'] + self.scaled_values['qhi']) / 2})"
        }
        exists = os.path.isfile(self.output)
        with open(self.output, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            if not exists:
                writer.writeheader()
            writer.writerow(data)

    def process_all_csv(self):
        for csv in os.listdir(self.sheet_folder):
            if csv.endswith(".csv"):
                self.process(csv)

                self.append_to_csv()

                self.global_vars = {"qhs": 0, "qp": 0, "qhi": 0, "att": 0}

def main():
    processor = SheetProcessor()
    processor.process_all_csv()

if __name__ == "__main__":
    main()
