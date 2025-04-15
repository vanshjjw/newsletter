from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS
import os
from processing.html_processor import process_html_content

app = Flask(__name__)

# Configure CORS
# Allow requests from the frontend development server
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})


@app.route('/api/process-manual', methods=['POST'])
def process_manual_email():
    # Check if the request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    html_content = data.get('html_content')

    if not html_content:
        return jsonify({"error": "Missing 'html_content' in request body"}), 400

    # Call the processing function
    result = process_html_content(html_content)

    if "error" in result:
        return jsonify(result), 500 # Or appropriate error code

    # Format the response
    processed_output = {
        "message": "Received and processed HTML content",
        **result # Unpack the results from the processor
    }
    return jsonify(processed_output)


# New endpoint to process the sample HTML file
@app.route('/api/process-sample', methods=['GET'])
def process_sample_email():
    sample_file_path = os.path.join(os.path.dirname(__file__), 'sample_email_alternate')

    try:
        with open(sample_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        return jsonify({"error": f"Sample file not found at {sample_file_path}. Please create it."}), 404
    except Exception as e:
        return jsonify({"error": f"Error reading sample file: {str(e)}"}), 500

    # Call the processing function
    result = process_html_content(html_content)

    if "error" in result:
        return jsonify(result), 500

    # Format the response
    processed_output = {
        "message": "Processed sample HTML content",
        "source_file": sample_file_path,
        **result
    }
    return jsonify(processed_output)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 