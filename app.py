from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
from cv_tracker import HandDexterityTracker
from ml_model import DexterityClassifier

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

tracker = HandDexterityTracker()
classifier = DexterityClassifier()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process video
            metrics = tracker.process_video(filepath)
            
            # Predict
            prediction = classifier.predict(metrics)
            metrics['diagnosis'] = prediction
            
            # Clean up
            os.remove(filepath)
            
            return jsonify(metrics)
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
