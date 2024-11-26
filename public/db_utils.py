import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extras import execute_values


def get_db_connection():
    conn = psycopg2.connect(
        dbname="sentiment",
        user="postgres",
        password="jd111322",
        host="localhost"
    )
    return conn


def insert_data_to_db(data):
    query = """INSERT INTO tagged_reviews (type, display_name, date, contents, categories, translated_content, 
    cleaned_data, neg, neu, pos, compound, sentiment) VALUES %s"""
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


def get_review_count_per_year(filters=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = "SELECT EXTRACT(YEAR FROM date) AS year, COUNT(*) AS count FROM tagged_reviews"
    conditions = []

    # Apply filters based on the provided filter parameters
    if filters:
        # Filter by category
        if 'category' in filters and filters['category'] and filters['category'] != 'all':
            conditions.append("categories = %(category)s")

        # Filter by month (ensure month is an integer)
        if 'month' in filters and filters['month'] and filters['month'] != 'all':
            try:
                conditions.append("EXTRACT(MONTH FROM date) = %(month)s")
            except ValueError:
                print(f"Invalid month value: {filters['month']}")  # Debugging invalid month value

        # Filter by years
        if 'years' in filters and filters['years'] and filters['years'] != 'all':
            years = filters['years']
            try:
                if years.strip():
                    years_list = [year.strip() for year in years.split(',') if year.strip().isdigit()]
                    if years_list:
                        if len(years_list) == 1:
                            conditions.append(f"EXTRACT(YEAR FROM date) = {years_list[0]}")
                        else:
                            years_list = tuple(map(int, years_list))
                            conditions.append(f"EXTRACT(YEAR FROM date) IN {years_list}")
            except ValueError:
                print("Invalid years format, skipping filter.")  # Handle error gracefully

    # Add conditions to query if there are any
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY year ORDER BY year"

    # Execute the query with the filters
    cursor.execute(query, filters)  # Pass the filters for proper parameterized queries
    reviews_per_year = cursor.fetchall()

    cursor.close()
    conn.close()

    return reviews_per_year


def get_peak_months(filters=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT EXTRACT(MONTH FROM date) AS month, COUNT(*) AS review_count
        FROM tagged_reviews
    """
    conditions = []

    # Apply filters if any
    if filters:
        # Filter by years if provided (allowing multiple years)
        if 'year' in filters and filters['year'] and filters['year'] != 'all':
            try:
                # Split years by commas, convert them to integers and apply IN clause
                years = [int(year.strip()) for year in filters['year'].split(',')]
                conditions.append(f"EXTRACT(YEAR FROM date) IN ({','.join(map(str, years))})")
            except ValueError:
                print(f"Invalid year value: {filters['year']}")  # Debugging invalid year value

        # Filter by category if provided
        if 'category' in filters and filters['category'] and filters['category'] != 'all':
            conditions.append(f"categories = '{filters['category']}'")

    # Add conditions to query if any filters were applied
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Group by month and order by month
    query += " GROUP BY month ORDER BY month"

    cursor.execute(query)
    peak_months = cursor.fetchall()

    cursor.close()
    conn.close()

    return peak_months


def get_reviews_by_category(filters=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT categories, 
               COUNT(*) FILTER (WHERE sentiment= 'positive') AS positive_count,
               COUNT(*) FILTER (WHERE sentiment= 'negative') AS negative_count
        FROM tagged_reviews
    """
    conditions = []

    # Apply filters if provided
    if filters:
        # Filter by years (multiple years allowed)
        if 'year' in filters and filters['year'] and filters['year'] != 'all':
            try:
                # Split the years by commas and convert them to integers
                years = [int(year.strip()) for year in filters['year'].split(',')]
                conditions.append(f"EXTRACT(YEAR FROM date) IN ({','.join(map(str, years))})")
            except ValueError:
                print(f"Invalid year value: {filters['year']}")  # Debugging invalid year value

        # Filter by month (if selected)
        if 'month' in filters and filters['month'] and filters['month'] != 'all':
            try:
                month = int(filters['month'])
                conditions.append(f"EXTRACT(MONTH FROM date) = {month}")
            except ValueError:
                print(f"Invalid month value: {filters['month']}")  # Debugging invalid month value

        # Filter by category (if provided)
        if 'category' in filters and filters['category'] and filters['category'] != 'all':
            conditions.append(f"categories = '{filters['category']}'")

    # Add conditions to the query if any filters are applied
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Group by categories
    query += " GROUP BY categories"

    cursor.execute(query)
    reviews_by_category = cursor.fetchall()

    cursor.close()
    conn.close()

    return reviews_by_category
