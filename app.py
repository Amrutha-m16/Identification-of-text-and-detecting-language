from flask import Flask, render_template, request,session, redirect, url_for,send_from_directory, flash
import os
import easyocr
from transformers import pipeline
from googletrans import Translator
from gtts import gTTS
from flask import Flask
from flask_cors import CORS
import sqlite3

# Initialize the Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'
CORS(app, origins=["/upload"], methods=["GET", "POST"], headers=["content-type"])
app.secret_key="123"

# Database connection
con=sqlite3.connect("language.db")
con.execute("create table if not exists user(pid integer primary key,name text,address text,contact integer,mail text)")
con.close()

# Function to extract text from an image using EasyOCR
def extract_text_from_image(image_path, languages, output_file):
    # Create an OCR reader instance with specified languages
    reader = easyocr.Reader(languages)

    try:
        # Use easyocr to extract text
        results = reader.readtext(image_path)
        # Combine the recognized text from different regions
        text = ' '.join(result[1] for result in results)
        # Write the filename and extracted text to the output file
        output_file.write(f"File: {image_path}\n")
        output_file.write(f"Extracted Text (easyocr):\n{text}\n")
        output_file.write("=" * 50 + "\n")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

# Language detection function
def detect_language(text):
    # Load the language detection model
    model_ckpt = "papluca/xlm-roberta-base-language-detection"
    pipe = pipeline("text-classification", model=model_ckpt)
    
    # Perform language detection
    output = pipe([text], top_k=1, truncation=True)

    # Extract label value from the output
    language_code = output[0][0]["label"]

    # Map language code to full language name
    language_mapping = {
        'ar': 'Arabic',
        'bg': 'Bulgarian',
        'de': 'German',
        'el': 'Greek',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'hi': 'Hindi',
        'it': 'Italian',
        'ja': 'Japanese',
        'nl': 'Dutch',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'sw': 'Swahili',
        'th': 'Thai',
        'tr': 'Turkish',
        'ur': 'Urdu',
        'vi': 'Vietnamese',
        'zh': 'Chinese'
    }

    # Get the full language name from the mapping
    language_name = language_mapping.get(language_code, 'Unknown')
    
    # Return the detected language name
    return language_name

# Language detection for words
def detect_language_for_words(text):
    # Split the string into words
    words = text.split()
    # Intialize an empty list to store detected languages for each word
    detected_languages = []

    # Detect language for each word
    for word in words:
        detected_languages.append(detect_language(word))

    return detected_languages

# Translation function
def translate_to_english(text, detected_language):
    translator = Translator()
    supported_languages = ['Arabic', 'Bulgarian', 'German', 'Greek', 'English', 'Spanish', 'French', 'Hindi', 'Italian', 'Japanese', 'Dutch', 'Polish', 'Portuguese', 'Russian', 'Swahili', 'Thai', 'Turkish', 'Urdu', 'Vietnamese', 'Chinese']
    
    if detected_language in supported_languages:
        # Convert the detected language to lowercase
        detected_language_lower = detected_language.lower()
        # Convert the detected language to its corresponding language code
        language_code_mapping = {
            'arabic': 'ar', 'bulgarian': 'bg', 'german': 'de', 'greek': 'el', 'english': 'en',
            'spanish': 'es', 'french': 'fr', 'hindi': 'hi', 'italian': 'it', 'japanese': 'ja',
            'dutch': 'nl', 'polish': 'pl', 'portuguese': 'pt', 'russian': 'ru', 'swahili': 'sw',
            'thai': 'th', 'turkish': 'tr', 'urdu': 'ur', 'vietnamese': 'vi', 'chinese': 'zh'
        }
        language_code = language_code_mapping.get(detected_language_lower)
        # Translate the text
        translated_text = translator.translate(text, dest='en').text
    else:
        translated_text = text
    
    return translated_text

#audio generation
def generate_combined_audio(translated_texts, filename):
    # Combine all translated texts into one single string
    combined_text = ' '.join(translated_texts)
    
    # Create a gTTS instance for the combined text
    tts = gTTS(text=combined_text, lang='en')
    
    # Generate a filename for the audio file based on the image filename
    audio_filename = f"{os.path.splitext(filename)[0]}.mp3"

    # Define the path to save the audio file in the `UPLOAD_FOLDER`
    audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    
    # Save the audio file in the specified `UPLOAD_FOLDER`
    tts.save(audio_file_path)
    
    # Return the filename of the saved audio file
    return audio_filename


# Home route
@app.route('/')
def index():
    return render_template('login.html')

# Login route
@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=='POST':
        name=request.form['name']
        password=request.form['password']
        con=sqlite3.connect("language.db")
        con.row_factory=sqlite3.Row
        cur=con.cursor()
        cur.execute("SELECT * FROM Login WHERE Username=? AND Password=?", (name, password))
        data=cur.fetchone()

        # if data:
        #     session["Username"]=data["Username"]
        #     return redirect("index.html")
        # else:
        #     flash("Username and Password Mismatch","danger")
    if request.method == 'GET':
        return render_template('index.html')
    return render_template('index.html',username = name)

# Register route
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        try:
            name=request.form['name']
            password=request.form['password']
            con=sqlite3.connect("language.db")
            cur=con.cursor()
            # cur.execute("insert into Register(Username,Password)values(?,?)",(name,password))
            cur.execute("insert into Login(Username,Password)values(?,?)",(name,password))
            con.commit()
            flash("Record Added  Successfully","success")
        except:
            flash("Error in Insert Operation","danger")
        finally:
            return render_template('login.html')
            con.close()

    return render_template('register.html')

# Upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return redirect(request.url)

    file = request.files['image']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Specifying the languages with Telugu and English
        languages = ['en', 'hi']
        
        # Output file path
        output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.txt')

        # Extract text from the image using easyocr
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            extract_text_from_image(file_path, languages, output_file)

        # Read input text from the output file
        input_text = ""
        with open(output_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) >= 3:
                third_line = lines[2]
                input_text = third_line

        # Detect language for each word in the input text
        detected_languages_for_words = detect_language_for_words(input_text)

        # Get the full language names corresponding to the language codes
        detected_languages_full = [detect_language(language_code) for language_code in detected_languages_for_words]

        # Translate detected text to English
        translated_text = [translate_to_english(text, detected_languages_for_words[i]) for i, text in enumerate(input_text.split())]
        
        # Generate audio for translated text
        audio_file_path = generate_combined_audio(translated_text, filename)


        # Clear the output file
        with open(output_file_path, 'w') as file:
            pass  # Do nothing, effectively clears the file

        # Render the result template with the detected languages and uploaded image
        detected_text_list = input_text.split()
        return render_template('result.html', filename=filename, detected_text=detected_text_list,
                               detected_languages=detected_languages_for_words, translated_text=translated_text,
                               audio_file_path=audio_file_path)


# Route to serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
