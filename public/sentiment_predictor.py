import pickle
import pandas as pd
from deep_translator import GoogleTranslator  # Updated import
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load the saved SVM model
with open('models/best_SVM_model_balanced.pkl', 'rb') as file:
    pipeline = pickle.load(file)

# Initialize the VADER sentiment analyzer and translator
analyzer = SentimentIntensityAnalyzer()
translator = GoogleTranslator(source='auto', target='en')  # Initialize translator for auto to English

def predict_sentiment(review_content):
    """Predicts the sentiment of a given review after translating it to English, with detailed sentiment scores."""
    
    # Translate review content to English
    try:
        translated_review = translator.translate(review_content)  # Translate directly to English
    except Exception as e:
        print(f"Translation error: {e}")
        translated_review = review_content  # Fall back to original if translation fails
    
    # Get VADER sentiment scores for the translated review
    scores = analyzer.polarity_scores(translated_review)
    neg_score = scores['neg']
    neu_score = scores['neu']
    pos_score = scores['pos']
    compound_score = scores['compound']
    
    # Prepare input data for the model
    input_data = pd.DataFrame({'Contents': [translated_review], 'compound': [compound_score]})
    
    # Predict sentiment using the loaded SVM model
    predicted_sentiment = pipeline.predict(input_data)[0]
    
    # Display translation, sentiment scores, and prediction
    print(f"\nTranslated Review: {translated_review}")
    print(f"Sentiment Scores:")
    print(f"  Negative: {neg_score}")
    print(f"  Neutral: {neu_score}")
    print(f"  Positive: {pos_score}")
    print(f"  Compound: {compound_score}")
    print(f"\nThe predicted sentiment for the review is: {predicted_sentiment}")
    
    return translated_review, neg_score, neu_score, pos_score, compound_score, predicted_sentiment

if __name__ == "__main__":
    # Prompt user for review input
    review_text = input("Please enter your review: ")
    
    # Predict sentiment
    predict_sentiment(review_text)
