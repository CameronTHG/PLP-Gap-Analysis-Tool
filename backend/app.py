from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import io
import os
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import functools
import urllib3

# Suppress only the InsecureRequestWarning from urllib3 needed for the Gemini API call
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- MONKEY PATCH FOR SSL VERIFICATION ---
# This forces all 'requests' library calls to disable SSL verification.
# A workaround for corporate proxies interfering with SSL certificates.
original_request = requests.Session.request

@functools.wraps(original_request)
def patched_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    return original_request(self, method, url, **kwargs)

requests.Session.request = patched_request
# --- END MONKEY PATCH ---

app = Flask(__name__)
CORS(app)

def get_embeddings(texts, api_key):
    """Generates embeddings for a list of texts."""
    try:
        # Configure to use REST transport. The monkey-patch above handles SSL.
        genai.configure(api_key=api_key, transport='rest')
        model = 'models/embedding-001'
        return genai.embed_content(model=model,
                                    content=texts,
                                    task_type="SEMANTIC_SIMILARITY")['embedding']
    except Exception as e:
        # Check for common authentication errors
        if "API key not valid" in str(e) or "permission" in str(e).lower():
            raise ValueError("Your Gemini API key is invalid or expired. Please check your key and try again.")
        else:
            raise ValueError(f"Failed to get embeddings: {e}")


@app.route('/api/find_opportunities', methods=['POST'])
def find_opportunities():
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key is missing.'}), 400
    if 'existing_pages' not in request.files or 'topic_attack' not in request.files:
        return jsonify({'error': 'Missing file(s)'}), 400

    existing_pages_file = request.files['existing_pages']
    topic_attack_file = request.files['topic_attack']

    try:
        # Read the raw bytes and decode manually to handle BOM correctly
        existing_pages_content = existing_pages_file.read().decode('utf-8-sig')
        topic_attack_content = topic_attack_file.read().decode('utf-8-sig')

        # Use StringIO to treat the decoded string as a file for pandas
        existing_df = pd.read_csv(io.StringIO(existing_pages_content))
        topic_df = pd.read_csv(io.StringIO(topic_attack_content))

        # Drop rows with missing values that are essential for processing
        existing_df.dropna(subset=['Keyword', 'Current position', 'Current URL'], inplace=True)
        topic_df.dropna(subset=['Keyword', 'Volume'], inplace=True)

        # Reset index after dropping rows to ensure iloc works correctly
        existing_df.reset_index(drop=True, inplace=True)
        topic_df.reset_index(drop=True, inplace=True)

        # Ensure dataframes are not empty after dropping NaNs
        if existing_df.empty or topic_df.empty:
            return jsonify({'error': 'CSV files are empty or became empty after removing rows with missing values.'}), 400

        # Validate required columns
        required_existing_cols = ['Keyword', 'Current position', 'Current URL']
        required_topic_cols = ['Keyword', 'Volume']

        if not all(col in existing_df.columns for col in required_existing_cols):
            return jsonify({'error': f'Existing pages CSV must contain the following columns: {", ".join(required_existing_cols)}'}), 400
        
        if not all(col in topic_df.columns for col in required_topic_cols):
            return jsonify({'error': f'Topic attack CSV must contain the following columns: {", ".join(required_topic_cols)}'}), 400

        opportunities = []
        
        # Get embeddings for all keywords
        existing_keywords = existing_df['Keyword'].tolist()
        topic_keywords = topic_df['Keyword'].tolist()

        existing_embeddings = get_embeddings(existing_keywords, api_key)
        topic_embeddings = get_embeddings(topic_keywords, api_key)

        # --- Keyword Consolidation using Embeddings ---
        
        # Calculate similarity between all topic keywords
        topic_similarity_matrix = cosine_similarity(topic_embeddings)
        
        processed_indices = set()
        groups = []
        consolidation_threshold = 0.90  # Similarity threshold for grouping

        for i in range(len(topic_keywords)):
            if i in processed_indices:
                continue

            # Find indices of keywords similar to the current one
            similar_indices = np.where(topic_similarity_matrix[i] >= consolidation_threshold)[0]
            
            # Create a new group with unprocessed keywords
            current_group_indices = [idx for idx in similar_indices if idx not in processed_indices]
            
            if not current_group_indices:
                continue

            # Mark these keywords as processed
            for idx in current_group_indices:
                processed_indices.add(idx)

            # Get the data for the current group
            group_df = topic_df.iloc[current_group_indices]
            
            # Consolidate volume for the group
            consolidated_volume = group_df['Volume'].sum()
            
            # Find the keyword with the highest volume to be the representative
            top_keyword_row = group_df.loc[group_df['Volume'].idxmax()]
            main_keyword = top_keyword_row['Keyword']
            
            # Store the original index of the main keyword for later
            main_keyword_original_index = top_keyword_row.name
            
            groups.append({
                'main_keyword': main_keyword,
                'consolidated_volume': consolidated_volume,
                'main_keyword_original_index': main_keyword_original_index
            })

        # --- Opportunity Analysis ---

        # Calculate similarity between the consolidated topic keywords and existing page keywords
        # We only need the similarity scores for the representative keywords
        main_keyword_indices = [g['main_keyword_original_index'] for g in groups]
        similarity_matrix = cosine_similarity(np.array(topic_embeddings)[main_keyword_indices], existing_embeddings)

        for i, group in enumerate(groups):
            # Find the best match in existing content for the representative keyword of the group
            best_match_score = np.max(similarity_matrix[i])
            best_match_index = np.argmax(similarity_matrix[i])

            # Set a threshold for similarity
            if best_match_score > 0.8:  # High similarity
                existing_row = existing_df.iloc[best_match_index]
                position = existing_row['Current position']

                if 5 <= position <= 20:
                    opportunities.append({
                        'Keyword': group['main_keyword'],
                        'Volume': group['consolidated_volume'],
                        'Action': 'Optimise Existing',
                        'Existing URL': existing_row['Current URL']
                    })
                elif position > 20:
                    opportunities.append({
                        'Keyword': group['main_keyword'],
                        'Volume': group['consolidated_volume'],
                        'Action': 'Create New Page',
                        'Existing URL': ''
                    })
                # If position is 0-4, we do nothing.

            else:  # Not similar enough to any existing keyword
                opportunities.append({
                    'Keyword': group['main_keyword'],
                    'Volume': group['consolidated_volume'],
                    'Action': 'Create New Page',
                    'Existing URL': ''
                })

        if not opportunities:
            return jsonify({'error': 'No opportunities found.'}), 404

        output_df = pd.DataFrame(opportunities)
        
        # Create a string buffer to hold the CSV data
        output_buffer = io.StringIO()
        output_df.to_csv(output_buffer, index=False)
        output_buffer.seek(0)

        # Create an in-memory binary stream
        mem_file = io.BytesIO()
        mem_file.write(output_buffer.getvalue().encode('utf-8'))
        mem_file.seek(0)
        output_buffer.close()


        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name='seo_opportunities.csv'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)