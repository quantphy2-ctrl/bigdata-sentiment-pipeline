import csv
from pathlib import Path

files = [
    Path("data/raw/Tweets.csv"),
    Path("data/raw/sentiment140/training.1600000.processed.noemoticon.csv"),
    Path("data/raw/sentiment140/testdata.manual.2009.06.14.csv"),
]

for path in files:
    print("\n" + "=" * 90)
    print("FILE:", path)

    if not path.exists():
        print("KHONG TIM THAY FILE")
        continue

    print("Size:", round(path.stat().st_size / 1024**2, 3), "MB")

    for encoding in ["utf-8-sig", "latin-1"]:
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                reader = csv.reader(f)

                print("Encoding:", encoding)

                if "Tweets.csv" in path.name:
                    header = next(reader)
                    print("\nCOLUMNS:")
                    for i, col in enumerate(header):
                        print(f"{i + 1}. {col}")

                    print("\nFIRST 5 RECORDS:")
                    for i, row in enumerate(reader):
                        if i >= 5:
                            break
                        print(f"\nRecord {i + 1}:")
                        for col, value in zip(header, row):
                            print(f"  {col}: {value[:250]}")

                else:
                    print("Expected columns: target, ids, date, flag, user, text")
                    print("\nFIRST 5 RECORDS:")
                    for i, row in enumerate(reader):
                        if i >= 5:
                            break
                        print(f"\nRecord {i + 1}:")
                        print(row)

            break

        except UnicodeDecodeError:
            print("Encoding khong phu hop:", encoding)

    else:
        print("Khong doc duoc file voi cac encoding thu nghiem.")
