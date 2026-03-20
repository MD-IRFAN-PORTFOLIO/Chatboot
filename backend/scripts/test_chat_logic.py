import re

def test_logic(user_message):
    search_terms = [word for word in user_message.split() if len(word) >= 3]
    print(f"Search terms: {search_terms}")
    if search_terms:
        regex_pattern = "|".join([re.escape(term) for term in search_terms])
        print(f"Regex pattern: {regex_pattern}")

if __name__ == "__main__":
    test_logic("who is HOD of ece")
    test_logic("test")
