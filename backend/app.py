from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

from processing.html_processor import process_html_content
# Import the new LLM summarizer function
from processing.llm.llm_summarizer import summarize_newsletter_content

app = Flask(__name__)

# Configure CORS
# Allow requests from the frontend development server
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Get API Key from environment variable
LLM_API_KEY = os.environ.get("GROQ_API_KEY") # Or your specific variable name

@app.route('/api/process-manual', methods=['POST'])
def process_manual_email():
    # Check if the request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    html_content = data.get('html_content')

    if not html_content:
        return jsonify({"error": "Missing 'html_content' in request body"}), 400

    # 1. Process HTML to get plain text
    processing_result = process_html_content(html_content)
    if "error" in processing_result:
        return jsonify(processing_result), 500

    plain_text = processing_result.get("plain_text", "")
    if not plain_text:
        return jsonify({"error": "Failed to extract plain text from HTML"}), 500

    # 2. Summarize the plain text using LLM
    summaries = summarize_newsletter_content(plain_text, LLM_API_KEY)

    # Check if summarization failed (e.g., missing API key)
    if summaries and isinstance(summaries, list) and len(summaries) > 0 and "error" in summaries[0]:
         return jsonify({"error": "Summarization failed", "details": summaries[0].get("details", "Unknown summarization error")}), 500

    # 3. Format the final response
    final_output = {
        "message": "Received, processed, and summarized HTML content",
        "summaries": summaries,
        "original_plain_text_length": len(plain_text), # Optional: include original text length
        # Optionally include the full plain_text if needed by frontend later
        # "original_plain_text": plain_text
    }
    return jsonify(final_output)


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

    # 1. Process HTML
    processing_result = process_html_content(html_content)
    if "error" in processing_result:
        return jsonify(processing_result), 500

    plain_text = processing_result.get("plain_text", "")
    if not plain_text:
        return jsonify({"error": "Failed to extract plain text from sample HTML"}), 500

    # 2. Summarize using LLM
    summaries = summarize_newsletter_content(plain_text, LLM_API_KEY)
    if summaries and isinstance(summaries, list) and len(summaries) > 0 and "error" in summaries[0]:
         return jsonify({"error": "Summarization failed", "details": summaries[0].get("details", "Unknown summarization error")}), 500

    # 3. Format response
    final_output = {
        "message": "Processed and summarized sample HTML content",
        "source_file": sample_file_path,
        "summaries": summaries,
        "original_plain_text_length": len(plain_text),
    }
    return jsonify(final_output)


if __name__ == '__main__':
    if not LLM_API_KEY:
        print("\n*** WARNING: LLM API Key (e.g., GROQ_API_KEY) not found in environment. Summarization will fail. ***\n")
    app.run(debug=True, host='0.0.0.0') 