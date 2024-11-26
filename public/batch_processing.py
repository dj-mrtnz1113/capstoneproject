import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from deep_translator import GoogleTranslator

# Download necessary NLTK resources
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

# Text preprocessing function
def utils_preprocess_text(text, flg_stemm=True, flg_lemm=True, lst_stopwords=None):
    # Clean the text: convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', str(text).lower().strip())
    
    # Tokenize the text into a list of words
    lst_text = text.split()
    
    # Remove stopwords if provided
    if lst_stopwords is not None:
        lst_text = [word for word in lst_text if word not in lst_stopwords]

    # Apply Stemming if specified
    if flg_stemm:
        ps = PorterStemmer()
        lst_text = [ps.stem(word) for word in lst_text]

    # Apply Lemmatization if specified
    if flg_lemm:
        lem = WordNetLemmatizer()
        lst_text = [lem.lemmatize(word) for word in lst_text]

    # Remove whitespaces and gibberish characters
    lst_text = [re.sub('\n', '', word) for word in lst_text]
    lst_text = [re.sub(r'[^\w\s]', '', word) for word in lst_text]

    # Return the cleaned text as a single string
    return " ".join(lst_text)

# Batch processing function to read, clean, and apply sentiment analysis
def batch_process(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path, encoding = 'cp437')

    df.columns = [col.lower() for col in df.columns]

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
    
    # Translate contents to English using Google Translator
    df['translated_content'] = df['contents'].apply(lambda x: GoogleTranslator(source='auto', target='en').translate(x))
    
    # Drop null and duplicates
    df.dropna(subset=['translated_content'], inplace=True)
    df.drop_duplicates(subset=['translated_content'], inplace=True)

    # Clean the translated content
    stopwords_en = stopwords.words("english")
    df['cleaned_data'] = df['translated_content'].apply(lambda x: utils_preprocess_text(x, flg_stemm=True, flg_lemm=True, lst_stopwords=stopwords_en))

    # Initialize the VADER sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()
    
    # Apply VADER sentiment analysis
    def apply_vader(text):
        sentiment_score = analyzer.polarity_scores(text)
        return sentiment_score
    
    # Apply VADER scores to the cleaned content
    df[['neg', 'neu', 'pos', 'compound']] = df['cleaned_data'].apply(apply_vader).apply(pd.Series)
    
    # Assign sentiment labels based on the compound score
    df['sentiment'] = df['compound'].apply(lambda x: 'positive' if x >= 0 else 'negative')

    # Return the processed dataframe
    return df

# Function to save the processed data to a new CSV file
def save_processed_data(df, output_path):
    df.to_csv(output_path, index=False)

# # Main function to process the batch and save the results
# if __name__ == "__main__":
#     input_file = "dataset/try_data.csv"  # Replace with your input file path
#     output_file = "path_to_output_file.csv"  # Replace with your desired output file path

#     # Process the batch
#     processed_df = batch_process(input_file)
    
#     # Save the processed data to a new file
#     save_processed_data(processed_df, output_file)

#     print(f"Processed data saved to {output_file}")