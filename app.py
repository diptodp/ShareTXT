from flask import Flask, render_template, request, session
from flask_session import Session
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the server
app.config['SECRET_KEY'] = 'your_secret_key'
Session(app)

text_data = {}

def generate_access_link():
    return str(datetime.now().timestamp())

def generate_user_id():
    return str(uuid.uuid4())

def is_valid_link(link):
    if link in text_data:
        timestamp = text_data[link]['timestamp']
        if datetime.now() - timestamp < timedelta(minutes=20):
            return True
        else:
            del text_data[link]
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    global text_data

    try:
        access_link = None
        user_id = session.get('user_id')

        if not user_id:
            user_id = generate_user_id()
            session['user_id'] = user_id

        if request.method == 'POST':
            text = request.form['text']
            existing_link = next((link for link, data in text_data.items() if data['user_id'] == user_id and is_valid_link(link)), None)
            
            if existing_link:
                access_link = existing_link
            else:
                access_link = generate_access_link()

            if access_link not in text_data:
                text_data[access_link] = {'user_id': user_id, 'timestamp': datetime.now(), 'texts': []}

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
                text = request.form['text']
                text_data[access_link]['texts'].append({'text': text, 'timestamp': datetime.now()})

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
