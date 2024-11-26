from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from sentiment_predictor import predict_sentiment
from db_utils import (
    get_review_count_per_year,
    get_peak_months,
    get_reviews_by_category,
    insert_data_to_db,
    get_db_connection
)
import os
import pandas as pd
from batch_processing import batch_process, save_processed_data 

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload and processed file directories
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Create necessary directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    review_content = data.get('review')
    
    if not review_content:
        return jsonify({"error": "No review content provided"}), 400
    
    try:
        # Use the predict_sentiment function from your sentiment_predictor module
        translated_review, neg_score, neu_score, pos_score, compound_score, predicted_sentiment = predict_sentiment(review_content)
        
        # Return the sentiment and scores in the expected format
        return jsonify({
            "sentiment": predicted_sentiment,
            "negative_score": neg_score,
            "neutral_score": neu_score,
            "positive_score": pos_score,
            "compound_score": compound_score
        }), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# Dashboard endpoints
@app.route('/dashboard/review_count_per_year', methods=['GET'])
def review_count_per_year():
    filters = {
        'category': request.args.get('category', 'all'),
        'month': request.args.get('month', 'all'),
        'years': request.args.get('years')  # This will be a comma-separated string or None
    }
    data = get_review_count_per_year(filters)
    return jsonify(data)


@app.route('/dashboard/peak_months', methods=['GET'])
def peak_months():
    try:
        # Get filters from request arguments (if any)
        filters = {
            'year': request.args.get('year', 'all'),
            'category': request.args.get('category', 'all')
        }

        # Fetch peak months with filters
        peak_month_data = get_peak_months(filters)

        return jsonify(peak_month_data), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route('/dashboard/reviews_by_category', methods=['GET'])
def reviews_by_category():
    try:
        # Get filters from request arguments (if any)
        filters = {
            'year': request.args.get('year', 'all'),
            'month': request.args.get('month', 'all'),
            'category': request.args.get('category', 'all')
        }

        # Fetch peak months with filters
        peak_month_data = get_reviews_by_category(filters)

        return jsonify(peak_month_data), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@app.route('/dashboard/years', methods=['GET'])
def get_years():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT EXTRACT(YEAR FROM date) AS year FROM tagged_reviews ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(years)

@app.route('/dashboard/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT categories FROM tagged_reviews ORDER BY categories")
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(categories)

@app.route('/dashboard/months', methods=['GET'])
def get_months():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the query to get distinct months
    cursor.execute("SELECT DISTINCT EXTRACT(MONTH FROM date) FROM tagged_reviews ORDER BY 1")

    # Fetch the result and handle None values
    months = [int(row[0]) for row in cursor.fetchall() if row[0] is not None]

    cursor.close()
    conn.close()

    return jsonify(months)

# File upload and batch processing endpoint
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})

    # Save the uploaded file to the uploads folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        # Process the file using the batch_process function
        processed_df = batch_process(file_path)

        # Save the processed file
        processed_file = os.path.join(app.config['PROCESSED_FOLDER'], f"processed_{file.filename}")
        save_processed_data(processed_df, processed_file)

        # Convert the processed DataFrame to a list of dictionaries for database insertion
        data = processed_df.to_dict(orient='records')

        # Insert the processed data into the database
        insert_data_to_db(data)

        # Check if the processed file exists
        if os.path.exists(processed_file):
            print(f"Processed file saved: {processed_file}")
        
        # Return download URL
        download_url = f"/download/{os.path.basename(processed_file)}"
        return jsonify({'success': True, 'download_url': download_url})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
    else:
        return jsonify({'success': False, 'message': 'File not found'}), 404


if __name__ == '__main__':
    app.run(port=5001, debug=True)