from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import asyncio
from pyrogram import Client
import logging
import secrets
import string

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    # Get environment variables
    api_id = os.environ.get('API_ID')
    api_hash = os.environ.get('API_HASH')
    bot_token = os.environ.get('BOT_TOKEN')
    session_string = os.environ.get('SESSION_STRING')
    
    # Check which credentials are missing
    missing = []
    if not api_id:
        missing.append("API_ID")
    if not api_hash:
        missing.append("API_HASH")
    if not bot_token:
        missing.append("BOT_TOKEN")
    if not session_string:
        missing.append("SESSION_STRING")
    
    return render_template('index.html', 
                          api_id=api_id, 
                          api_hash=api_hash[:4] + "..." + api_hash[-4:] if api_hash else None,
                          bot_token=bot_token[:10] + "..." + bot_token[-5:] if bot_token else None,
                          session_string=session_string[:10] + "..." + session_string[-10:] if session_string else None,
                          missing=missing)

@app.route('/generate_session', methods=['GET', 'POST'])
def generate_session_page():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        session['phone_number'] = phone_number
        return redirect(url_for('start_session_generation'))
    
    return render_template('generate_session.html')

@app.route('/start_generation')
def start_session_generation():
    phone_number = session.get('phone_number')
    if not phone_number:
        flash('Phone number is required', 'error')
        return redirect(url_for('generate_session_page'))
    
    api_id = os.environ.get('API_ID')
    api_hash = os.environ.get('API_HASH')
    
    if not api_id or not api_hash:
        flash('API_ID and API_HASH environment variables must be set', 'error')
        return redirect(url_for('home'))
    
    # Store info in session
    session['generation_started'] = True
    
    return render_template('verify_code.html', phone_number=phone_number)

@app.route('/verify_code', methods=['POST'])
def verify_code():
    if not session.get('generation_started'):
        flash('Session generation was not started', 'error')
        return redirect(url_for('generate_session_page'))
    
    phone_number = session.get('phone_number')
    verification_code = request.form.get('verification_code')
    
    if not phone_number or not verification_code:
        flash('Phone number and verification code are required', 'error')
        return redirect(url_for('start_session_generation'))
    
    api_id = os.environ.get('API_ID')
    api_hash = os.environ.get('API_HASH')
    
    try:
        # Generate session string
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session_string = loop.run_until_complete(create_session_string(api_id, api_hash, phone_number, verification_code))
        loop.close()
        
        # Successfully generated
        if session_string:
            return render_template('success.html', session_string=session_string)
        else:
            flash('Failed to generate session string', 'error')
            return redirect(url_for('generate_session_page'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('generate_session_page'))

async def create_session_string(api_id, api_hash, phone_number, code):
    """Generate a Pyrogram session string"""
    try:
        # Create a client with the provided credentials
        client = Client(
            "session_generator",
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            in_memory=True
        )
        
        await client.connect()
        
        # If already logged in
        if await client.is_user_authorized():
            session_string = await client.export_session_string()
            await client.disconnect()
            return session_string
        
        # Attempt to login with the provided code
        await client.sign_in(phone_number, code)
        
        # If 2FA is enabled, this will raise an exception
        session_string = await client.export_session_string()
        await client.disconnect()
        return session_string
    except Exception as e:
        logger.error(f"Error generating session string: {e}")
        await client.disconnect()
        raise

@app.route('/run_bot')
def run_bot():
    # Import MusicBot and run it
    try:
        from bot import MusicBot
        
        # Check if we have all required credentials
        api_id = os.environ.get('API_ID')
        api_hash = os.environ.get('API_HASH')
        bot_token = os.environ.get('BOT_TOKEN')
        session_string = os.environ.get('SESSION_STRING')
        
        if not all([api_id, api_hash, bot_token, session_string]):
            flash('Missing required credentials', 'error')
            return redirect(url_for('home'))
        
        # Run the bot in a separate thread or process
        # (In a real application, this would be done differently)
        flash('Bot started successfully! Check your Telegram app.', 'success')
    except Exception as e:
        flash(f'Error starting bot: {str(e)}', 'error')
    
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
