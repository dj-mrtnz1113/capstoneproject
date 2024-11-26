import requests

# URL of your endpoint
url = 'http://127.0.0.1:5001/upload_batch'

# Open the file to upload (replace 'path_to_your_file.csv' with the actual path to the CSV file you want to test)
with open('dataset/try_data.csv', 'rb') as file:
    # Send a POST request with the file
    response = requests.post(url, files={'file': file})

# Print the response status and body
print(response.status_code)  # Should print 200 if successful
print(response.json())  # This will print the JSON response from your API
