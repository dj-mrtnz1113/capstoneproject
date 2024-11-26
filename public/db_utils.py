import psycopg2
from psycopg2.extras import RealDictCursor
from collections import Counter
from psycopg2.extras import execute_values
import datetime

def get_db_connection():
    conn = psycopg2.connect(
        dbname="sentiment",
        user="postgres",
        password="jd111322",
        host="localhost"
    )
    return conn

# Insert batch of processed data
def insert_data_to_db(data):
    query = """
    INSERT INTO tagged_reviews (type, display_name, date, contents, categories, translated_content, cleaned_data, neg, neu, pos, compound, sentiment)
    VALUES %s
    """
    # Extract data as tuples for insertion
    values = [
        (
            row['type'],
            row['display_name'],
            row['date'],
            row['contents'],
            row['categories'],
            row['translated_content'],  # Include translated content here
            row['cleaned_data'],
            row['neg'],
            row['neu'],
            row['pos'],
            row['compound'],
            row['sentiment']
        )
        for row in data
    ]
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            execute_values(cur, query, values)
            conn.commit()
        print("Data successfully inserted.")
    except psycopg2.Error as db_error:
        print("Database error:", db_error)
    except Exception as e:
        print("Unexpected error:", e)
    finally:
        if conn:
            conn.close()

# Function to get the count of reviews per year
def get_review_count_per_year():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT EXTRACT(YEAR FROM date) AS year, COUNT(*) AS count FROM tagged_reviews GROUP BY year ORDER BY year")
    reviews_per_year = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return reviews_per_year

# Function to get the peak months of reviews
def get_peak_months():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT EXTRACT(MONTH FROM date) AS month, COUNT(*) AS review_count
        FROM tagged_reviews
        GROUP BY month
        ORDER BY month
    """)
    peak_months = cursor.fetchall()

    cursor.close()
    conn.close()

    return peak_months

# Function to get positive and negative reviews by category
def get_reviews_by_category():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT categories, 
               COUNT(*) FILTER (WHERE sentiment= 'positive') AS positive_count,
               COUNT(*) FILTER (WHERE sentiment= 'negative') AS negative_count
        FROM tagged_reviews
        GROUP BY categories
    """)
    reviews_by_category = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return reviews_by_category

