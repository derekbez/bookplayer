import csv
import logging
import config

logger = logging.getLogger(__name__)

class BookList:
    def __init__(self, file_path=config.booklist_filepath):
        self.file_path = file_path

    def validate_card_id(self, card_id: str) -> bool:
        """Validate that the card ID is numeric and of correct length."""
        if not card_id.isdigit():
            return False
        length = len(card_id)
        return 1 <= length <= 16

    def get_bookid_from_cardid(self, card_id):
        """
        Get book title from card ID.
        
        Args:
            card_id: String representation of the card ID number
            
        Returns:
            int: book_id if found, None otherwise
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
                            # Use the card_id as the book_id since they have a 1:1 relationship
                            return int(file_card_id)
                        except ValueError as e:
                            logger.error(f"Error converting card_id to book_id: {e}")
                            return None

                logger.info(f"Card ID {card_id} not found in booklist")
                return None

        except FileNotFoundError:
            logger.error(f"Booklist file not found: {self.file_path}")
            return None
        except csv.Error as e:
            logger.error(f"CSV parsing error in {self.file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading booklist: {e}")
            return None

    def check_file_format(self):
        """
        Validate the entire CSV file format.
        Returns a tuple of (is_valid, list of errors).
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

# Usage example:
if __name__ == "__main__":
    file_reader = BookList('/home/rpi/books/booklist.csv')

    # Get value by key
    print(file_reader.get_bookid_from_cardid(1243471995817856))

    # Check for file format validity
    is_valid, errors = file_reader.check_file_format()
    if is_valid:
        print("CSV file format is valid.")
    else:
        print("CSV file format has errors:")
        for error in errors:
            print(error)
