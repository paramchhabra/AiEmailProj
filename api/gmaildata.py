import os
import flask
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests
import base64
from bs4 import BeautifulSoup

# Flask app setup
app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

# Path to client_secret.json, this is downloaded from Google Cloud console
CLIENT_SECRETS_FILE = "api\client.json"

# Scopes required to read the user's Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'

# The endpoint for the home page
@app.route('/')
def index():
    return "Hello world"

# The endpoint to authorize the user
@app.route('/authorize')
def authorize():
    # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=flask.url_for('oauth2callback', _external=True)
    )

    # Generate authorization URL for the user to grant access
    authorization_url, state = flow.authorization_url(
        access_type='offline', 
        include_granted_scopes='true'
    )

    # Store the state in the session to validate later
    flask.session['state'] = state

    return flask.redirect(authorization_url)

# Callback endpoint where Google redirects after user authentication
@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session.get('state')
    if not state:
        return 'State not found in session.', 400

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=flask.url_for('oauth2callback', _external=True)
    )

    try:
        flow.fetch_token(authorization_response=flask.request.url)
    except Exception as e:
        return f"An error occurred while fetching the token: {e}"

    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('gmail_data'))


@app.route('/gmail_data')
def gmail_data():
    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])

    # Build the Gmail service
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    try:
        # Retrieve the first batch of messages (up to 1000)
        results = service.users().messages().list(userId='me', maxResults=1000).execute()
        messages = results.get('messages', [])

        if not messages:
            return "No new emails."
        email_data = []
        for message in messages[:50]:  # Limit to the first 10 emails
            
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg['payload'].get('headers', [])

            # Extract relevant email headers
            email_details = {
                "subject": next((header['value'] for header in headers if header['name'] == 'Subject'), "No Subject"),
                "from": next((header['value'] for header in headers if header['name'] == 'From'), "Unknown Sender"),
                "date": next((header['value'] for header in headers if header['name'] == 'Date'), "Unknown Date"),
            }

            # Get the full message body, handling parts
            email_details["message"] = get_email_body(msg['payload'])
            
            index = 0

            if email_details["message"].rfind("Vellore Institute of Technology (VIT), India -")==-1:
                index = len(email_details["message"])
            else:
                index = email_details["message"].rfind("Vellore Institute of Technology (VIT), India -")

            # Append email details to the email_data list
            email_data.append(
                f"Subject: {email_details['subject']}Date: {email_details['date']}Message: {email_details['message'][:index]}"
            )


        return '<br><br><br>'.join(email_data)

    except googleapiclient.errors.HttpError as error:
        return f"An error occurred: {error}"
    

def get_email_body(payload):
    """
    Extract the body of an email, handling both HTML and plain text formats.
    """
    html_body = None
    plain_text_body = None

    if 'parts' in payload:
        for part in payload['parts']:
            # Handle multipart/alternative MIME type with sub-parts
            if part['mimeType'] == 'multipart/alternative' and 'parts' in part:
                for subpart in part['parts']:
                    if subpart['mimeType'] == 'text/html' and 'data' in subpart['body']:
                        html_body = decode_base64(subpart['body']['data'])
                    elif subpart['mimeType'] == 'text/plain' and 'data' in subpart['body']:
                        plain_text_body = decode_base64(subpart['body']['data'])
            # Handle normal HTML parts
            elif part['mimeType'] == 'text/html' and 'data' in part['body']:
                html_body = decode_base64(part['body']['data'])
            # Handle normal text/plain parts
            elif part['mimeType'] == 'text/plain' and 'data' in part['body']:
                plain_text_body = decode_base64(part['body']['data'])
            # Handle nested parts recursively
            elif 'parts' in part:
                nested_body = get_email_body(part)
                if nested_body:  # If found nested body, return that
                    return nested_body

    # Handle the case where the email body is directly in the payload
    if 'data' in payload['body']:
        if payload['mimeType'] == 'text/html':
            html_body = decode_base64(payload['body']['data'])
        elif payload['mimeType'] == 'text/plain':
            plain_text_body = decode_base64(payload['body']['data'])

    # If we have HTML content, extract text from it
    if html_body:
        return extract_text_from_html(html_body)
    # Otherwise, return the plain text content
    elif plain_text_body:
        return plain_text_body
    else:
        return "No content found."


def decode_base64(data):
    """
    Decode base64 data, ensuring that it is padded correctly.
    """
    # Add missing padding if necessary
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)

    try:
        decoded_bytes = base64.urlsafe_b64decode(data)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        print(f"Error decoding base64 data: {e}")
        return None


def extract_text_from_html(html):
    """
    Remove all HTML tags and extract the visible text content from the body.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract the text from the <body> tag, if present
    body = soup.find('body')
    if body:
        # Get text inside the body, stripping all tags and keeping the text content
        return body.get_text(separator='\n', strip=True)
    else:
        # If no body tag, extract text from the whole HTML content
        return soup.get_text(separator='\n', strip=True)
# Revoke token endpoint
@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to authorize before revoking tokens.', 400)

    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
    revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    if revoke.status_code == 200:
        return 'Tokens successfully revoked.'
    else:
        return 'Failed to revoke tokens.'

# Helper function to convert credentials to a dictionary
def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    app.run(host='localhost', port=5000, ssl_context=('api\cert.pem', 'api\key.pem'), debug=True)

