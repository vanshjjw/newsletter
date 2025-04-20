import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()


from core.html_parser import parse_html_to_text
from core.summarisation import summarize_newsletter

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

LLM_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/')
def hello():
    return jsonify(message="Newsletter Backend is running!"), 200


@app.route('/api/process-sample', methods=['GET'])
def process_sample_email():
    sample_file_path = os.path.join(os.path.dirname(__file__), 'sample_email')

    try:
        with open(sample_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        return jsonify({"error": f"Error reading sample file."}), 500


    parsing_result = parse_html_to_text(html_content)
    if "error" in parsing_result:
        return jsonify(parsing_result), 500


    plain_text = parsing_result.get("plain_text", "")
    if not plain_text:
        return jsonify({"summaries": [], "message": "HTML processed, but no content found."}), 200


    summaries_data = summarize_newsletter(plain_text, LLM_API_KEY)
    if summaries_data and isinstance(summaries_data, list) and len(summaries_data) > 0 and summaries_data[0].get("error"): 
         return jsonify({"error": "Summarization Failed", "details": summaries_data[0].get("details", "Unknown error during summarization")}), 500


    final_output = {
        "message": "Processed and summarized sample HTML content",
        "source_file": sample_file_path,
        "summaries": summaries_data,
        "original_plain_text_length": len(plain_text),
    }
    return jsonify(final_output)


if __name__ == '__main__':
    app.run(debug=True) 