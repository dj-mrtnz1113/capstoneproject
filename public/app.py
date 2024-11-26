from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from sentiment_predictor import predict_sentiment
from db_utils import (
    get_review_count_per_year,
    get_peak_months,
    get_reviews_by_category,
    insert_data_to_db
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
    try:
        data = get_review_count_per_year()
        return jsonify(data), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@app.route('/dashboard/peak_months', methods=['GET'])
def peak_months():
    try:
        peak_month_data = get_peak_months()
        return jsonify(peak_month_data), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route('/dashboard/reviews_by_category', methods=['GET'])
def reviews_by_category():
    try:
        data = get_reviews_by_category()  # Use the updated function to get both positive and negative counts
        return jsonify(data), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


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