from flask import Flask, render_template, request, session
from flask_session import Session
from datetime import datetime, timedelta
import uuid
import redis

app = Flask(__name__)

# Set the Flask app secret key
app.secret_key = '121121121'  # Replace with a secure key

# Configure session storage for server-side persistence using Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'your_prefix_here'  # Optional: Add a key prefix
app.config['SESSION_REDIS'] = redis.StrictRedis.from_url('redis://localhost:6379/0')  # Adjust Redis URL if needed

Session(app)

def generate_user_id():
    return str(uuid.uuid4())

def generate_access_link(user_id):
    # Using a combination of user_id and a random UUID for uniqueness
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{user_id}-{uuid.uuid4()}"))

# A dictionary to store data (replace this with database models later)
text_data = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        access_link = None
        user_id = session.get('user_id')

        if not user_id:
            user_id = generate_user_id()
            session['user_id'] = user_id

        if request.method == 'POST':
            text = request.form['text']
            existing_link = next((link for link, data in text_data.items() if data['user_id'] == user_id), None)

            if existing_link:
                access_link = existing_link
            else:
                access_link = generate_access_link(user_id)

            if access_link not in text_data:
                text_data[access_link] = {'user_id': user_id, 'timestamp': datetime.now(), 'texts': []}

            text_data[access_link]['texts'].append({'text': text, 'timestamp': datetime.now()})
    except Exception as e:
        print(f"Error in index route: {str(e)}")

    return render_template('index.html', access_link=access_link)

@app.route('/access/<access_link>', methods=['GET', 'POST'])
def access_text(access_link):
    try:
        if access_link in text_data and text_data[access_link]['user_id'] == session.get('user_id'):
            if request.method == 'POST':
                text = request.form['text']
                text_data[access_link]['texts'].append({'text': text, 'timestamp': datetime.now()})

            texts = text_data[access_link]['texts']
            return render_template('access.html', texts=texts, access_link=access_link)
        else:
            return "Invalid or expired access link."
    except Exception as e:
        print(f"Error in access_text route: {str(e)}")
        return "Internal Server Error"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

