import re
import mysql.connector
from core.database import db_config

def check_keywords_match(text: str) -> str:
    """
    Check if the text matches any keyword in the database.
    Returns the response message if matched, else None.
    """
    try:
        connection = db_config.get_connection()
        if not connection:
            print("Warning: Cannot connect to database")
            return None
            
        cursor = connection.cursor(dictionary=True)
        
        # Query all enabled keywords, ordered by priority
        query = """
        SELECT keyword, match_type, response_message 
        FROM keywords 
        WHERE enabled = 1 
        ORDER BY priority DESC, id ASC
        """
        
        cursor.execute(query)
        keywords = cursor.fetchall()
        
        # Check each keyword
        for keyword_data in keywords:
            keyword = keyword_data['keyword']
            match_type = keyword_data['match_type']
            response = keyword_data['response_message']
            
            # Match based on type
            is_match = False
            if match_type == 'exact':
                # Exact match
                if text.strip() == keyword:
                    is_match = True
            elif match_type == 'contains':
                # Contains match
                if keyword in text:
                    is_match = True
            elif match_type == 'regex':
                # Regex match
                keywords_list = keyword.split('|')
                for k in keywords_list:
                    if k.strip() and re.search(k.strip(), text, re.IGNORECASE):
                        is_match = True
                        break
            
            # If matched, return response
            if is_match:
                cursor.close()
                connection.close()
                return response
                
        cursor.close()
        connection.close()
        return None
        
    except mysql.connector.Error as err:
        print(f"Database query error: {err}")
        return None
    except Exception as e:
        print(f"Error checking keyword match: {e}")
        return None
