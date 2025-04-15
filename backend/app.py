from flask import Flask, request, jsonify
import os

app = Flask(__name__)


@app.route('/api/process-manual', methods=['POST'])
def process_manual_email():
    # Check if the request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    html_content = data.get('html_content')

    if not html_content:
        return jsonify({"error": "Missing 'html_content' in request body"}), 400

    # --- Placeholder for Processing Logic ---
    # 1. Parse HTML (e.g., using BeautifulSoup)
    # 2. Chunk content into articles
    # 3. Summarize/Generate headlines
    # For now, just return the received HTML length as confirmation
    processed_output = {
        "message": "Received HTML content",
        "html_length": len(html_content),
        "processed_chunks": [] # Placeholder for actual results
    }
    # ----------------------------------------
    return jsonify(processed_output)


# New endpoint to process the sample HTML file
@app.route('/api/process-sample', methods=['GET'])
def process_sample_email():
    sample_file_path = os.path.join(os.path.dirname(__file__), 'sample_email.html')

    try:
        with open(sample_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        return jsonify({"error": f"Sample file not found at {sample_file_path}. Please create it."}), 404
    except Exception as e:
        return jsonify({"error": f"Error reading sample file: {str(e)}"}), 500

    # --- Placeholder for Processing Logic (Same as manual endpoint for now) ---
    # 1. Parse HTML (e.g., using BeautifulSoup)
    # 2. Chunk content into articles
    # 3. Summarize/Generate headlines
    processed_output = {
        "message": "Processed sample HTML content",
        "source_file": sample_file_path,
        "html_length": len(html_content),
        "processed_chunks": [] # Placeholder for actual results
    }
    # ----------------------------------------

    return jsonify(processed_output)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 