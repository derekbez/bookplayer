import csv
import config

class BookList:
    def __init__(self, file_path=config.booklist_filepath):
        self.file_path = file_path

    def get_bookid_from_cardid(self, card_id):
        try:
            with open(self.file_path, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if int(row[0]) == card_id:
                        return row[1].strip()
                return None
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")
            return None
        except ValueError:
            print("Error reading the key. Ensure the key is a valid integer.")
            return None

    def check_uniqueness_and_validity(self):
        try:
            with open(self.file_path, 'r') as file:
                reader = csv.reader(file)
                ids = set()
                for row in reader:
                    try:
                        key = int(row[0])
                        if key in ids:
                            print(f"Duplicate ID found: {key}")
                        ids.add(key)
                    except ValueError:
                        print(f"Invalid ID found: {row[0]}")
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")

# Usage example:
if __name__ == "__main__":
    file_reader = BookList('/home/rpi/repo/books/booklist.csv')

    # Get value by key
    print(file_reader.get_bookid_from_cardid(1243471995817856))

    # Check for uniqueness and valid IDs
    file_reader.check_uniqueness_and_validity()
