import csv
import logging
import config

logger = logging.getLogger(__name__)

class BookList:
    """
    Handles the mapping between RFID card IDs and book titles/IDs using a CSV file.
    Provides validation and lookup utilities for card IDs and book entries.
    """
    def __init__(self, file_path=config.booklist_filepath):
        self.file_path = file_path

    def validate_card_id(self, card_id: str) -> bool:
        """
        Check if the card ID is numeric and within the expected length (1-16 digits).
        Args:
            card_id (str): The card ID to validate.
        Returns:
            bool: True if valid, False otherwise.
        """
        if not card_id.isdigit():
            return False
        length = len(card_id)
        return 1 <= length <= 16

    def get_bookid_from_cardid(self, card_id):
        """
        Look up the book ID and title for a given RFID card ID from the CSV file.
        Args:
            card_id (str): The card ID to look up.
        Returns:
            tuple: (book_id as int, book_title as str) if found, else (None, None)
        """
        try:
            with open(self.file_path, 'r') as file:
                reader = csv.reader(file)
                # Skip header row
                next(reader, None)

                for line_num, row in enumerate(reader, 1):
                    # Check row format
                    if len(row) != 2:
                        logger.error(f"Invalid CSV format at line {line_num}: expected 2 columns, got {len(row)}")
                        continue

                    file_card_id, book_title = row[0].strip(), row[1].strip()
                    logger.debug(f"Comparing card ID {card_id} with file card ID {file_card_id}")

                    # Validate card ID format
                    if not self.validate_card_id(file_card_id):
                        logger.error(f"Invalid card ID format at line {line_num}: {file_card_id}")
                        continue

                    # Validate book title
                    if not book_title:
                        logger.error(f"Empty book title at line {line_num}")
                        continue

                    if file_card_id == str(card_id):
                        logger.info(f"Found matching card ID: {card_id} -> {book_title}")
                        try:
                            return int(file_card_id), book_title
                        except ValueError as e:
                            logger.error(f"Error converting card_id to book_id: {e}")
                            return None, None

                logger.info(f"Card ID {card_id} not found in booklist")
                return None, None

        except FileNotFoundError:
            logger.error(f"Booklist file not found: {self.file_path}")
            return None, None
        except csv.Error as e:
            logger.error(f"CSV parsing error in {self.file_path}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error reading booklist: {e}")
            return None, None

    def check_file_format(self):
        """
        Validate the format of the entire booklist CSV file.
        Returns:
            tuple: (is_valid (bool), list of error messages)
        """
        errors = []
        try:
            with open(self.file_path, 'r') as file:
                reader = csv.reader(file)
                # Skip header row
                next(reader, None)

                for line_num, row in enumerate(reader, 1):
                    if len(row) != 2:
                        errors.append(f"Line {line_num}: Expected 2 columns, got {len(row)}")
                        continue

                    card_id, title = row[0].strip(), row[1].strip()

                    if not self.validate_card_id(card_id):
                        errors.append(f"Line {line_num}: Invalid card ID format: {card_id}")

                    if not title:
                        errors.append(f"Line {line_num}: Empty book title")

            return len(errors) == 0, errors

        except FileNotFoundError:
            return False, ["Booklist file not found"]
        except csv.Error as e:
            return False, [f"CSV parsing error: {e}"]
        except Exception as e:
            return False, [f"Unexpected error: {e}"]

if __name__ == "__main__":
    import logging
    import os
    import config
    import sys

    def list_folders(booklist_dir):
        print(f"\nFolders in {booklist_dir}:")
        folders = []
        try:
            for entry in os.listdir(booklist_dir):
                full_path = os.path.join(booklist_dir, entry)
                if os.path.isdir(full_path):
                    print(f"  [DIR] {entry}")
                    folders.append(entry)
        except Exception as e:
            print(f"Error listing folders: {e}")
        return set(folders)

    def check_csv_validity(blist):
        is_valid, errors = blist.check_file_format()
        if is_valid:
            print("CSV file format is valid.")
        else:
            print("CSV file format has errors:")
            for error in errors:
                print(error)
        return is_valid

    def print_csv_contents(booklist_path):
        print(f"\nContents of {booklist_path}:")
        csv_titles = set()
        last_card_id = None
        try:
            with open(booklist_path, 'r') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    line = ','.join(row)
                    print(line.strip())
                    if i == 0:
                        continue  # skip header for titles
                    if len(row) == 2:
                        csv_titles.add(row[1].strip())
                        last_card_id = row[0].strip()
        except Exception as e:
            print(f"Error reading booklist file: {e}")
        return csv_titles, last_card_id

    def print_deviations(csv_titles, folder_names):
        print("\nChecking that all book titles in CSV match folder names:")
        missing_folders = csv_titles - folder_names
        extra_folders = folder_names - csv_titles

        if missing_folders:
            print(f"Folders missing for these CSV book titles: {sorted(missing_folders)}")
        else:
            print("All CSV book titles have matching folders.")

        if extra_folders:
            print(f"Folders present with no matching CSV entry: {sorted(extra_folders)}")
        else:
            print("No extra folders found.")

        if len(csv_titles) > len(folder_names):
            print(f"There are more entries in the CSV ({len(csv_titles)}) than folders ({len(folder_names)}).")
        elif len(folder_names) > len(csv_titles):
            print(f"There are more folders ({len(folder_names)}) than entries in the CSV ({len(csv_titles)}).")
        else:
            print("The number of folders matches the number of CSV entries.")

    def test_card_ids(blist, last_card_id):
        print("\nLookup with invalid card ID '999':")
        book_id, book_title = blist.get_bookid_from_cardid("999")
        if book_id is not None:
            print(f"Book ID: {book_id}, Title: {book_title}")
        else:
            print("Card ID '999' not found.")

        if last_card_id:
            print(f"\nLookup with last card ID from CSV: {last_card_id}")
            book_id, book_title = blist.get_bookid_from_cardid(last_card_id)
            if book_id is not None:
                print(f"Book ID: {book_id}, Title: {book_title}")
            else:
                print(f"Card ID '{last_card_id}' not found.")
        else:
            print("No valid card IDs found in CSV.")

    def main():
        logger = logging.getLogger("booklist.__main__")
        logging.basicConfig(level=logging.INFO)

        # Use config for file path
        booklist_path = config.booklist_filepath
        booklist_dir = os.path.dirname(booklist_path)
        logger.info(f"Using booklist file: {booklist_path}")
        blist = BookList(booklist_path)

        # 1. List folders
        folder_names = list_folders(booklist_dir)

        # 2. Test if CSV is valid
        check_csv_validity(blist)

        # 3. Print contents of CSV
        csv_titles, last_card_id = print_csv_contents(booklist_path)

        # 4. Deviations between CSV and folders
        print_deviations(csv_titles, folder_names)

        # 5. Test invalid card id, test valid card id
        test_card_ids(blist, last_card_id)

    main()
