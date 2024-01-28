

from flask import Flask, render_template, request, session
from datetime import datetime, timedelta
import uuid  # Import uuid for generating unique user IDs

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Dictionary to store text data with access links and timestamps
text_data = {}

# Function to generate a unique access link
def generate_access_link():
    return str(datetime.now().timestamp())

# Function to generate a unique user ID
def generate_user_id():
    return str(uuid.uuid4())

# Function to check if the access link is valid and within the time limit
def is_valid_link(link):
    if link in text_data:
        timestamp = text_data[link]['timestamp']
        if datetime.now() - timestamp < timedelta(minutes=20):
            return True
        else:
            # If the link has expired, remove it from the dictionary
            del text_data[link]
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    global text_data

    try:
        access_link = None
        user_id = session.get('user_id')

        if not user_id:
            # If user doesn't have an ID, generate one
            user_id = generate_user_id()
            session['user_id'] = user_id

        if request.method == 'POST':
            text = request.form['text']

            # If there's an existing link and it's still valid, use it
            existing_link = next((link for link, data in text_data.items() if data['user_id'] == user_id and is_valid_link(link)), None)
            if existing_link:
                access_link = existing_link
            else:
                # Generate a new access link
                access_link = generate_access_link()

            # Store the text data with access link, timestamp, and texts
            if access_link not in text_data:
                text_data[access_link] = {'user_id': user_id, 'timestamp': datetime.now(), 'texts': []}

            # Append the new text to the list of texts
            text_data[access_link]['texts'].append({'text': text, 'timestamp': datetime.now()})
    except Exception as e:
        print(f"Error in index route: {str(e)}")

    return render_template('index.html', access_link=access_link)

@app.route('/access/<access_link>', methods=['GET', 'POST'])
def access_text(access_link):
    global text_data

    try:
        if is_valid_link(access_link) and text_data[access_link]['user_id'] == session.get('user_id'):
            if request.method == 'POST':
                # Update the list of texts for live pasting
                text = request.form['text']
                text_data[access_link]['texts'].append({'text': text, 'timestamp': datetime.now()})

            # Filter out texts that are older than 20 minutes
            texts = [item for item in text_data[access_link]['texts']
                    if datetime.now() - item['timestamp'] < timedelta(minutes=20)]

            return render_template('access.html', texts=texts, access_link=access_link)
        else:
            return "Invalid or expired access link."
    except Exception as e:
        print(f"Error in access_text route: {str(e)}")
        return "Internal Server Error"


if __name__ == '__main__':
    app.run(debug=True)
