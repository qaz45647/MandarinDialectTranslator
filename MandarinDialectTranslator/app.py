# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_from_directory
import google.generativeai as genai
import spacy
import pandas as pd
app = Flask(__name__)

# 載入模型
nlp_zh = spacy.load('zh_core_web_trf')

def configure_genai(api_key_file):
    with open(api_key_file, 'r') as file:
        api_key = file.read().strip()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def load_data(file_name):
    return pd.read_csv(file_name)

def filter_words(prompt, nlp_model):
    doc = nlp_model(prompt)
    filtered_words = [token.text for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'NUM']]
    return list(set(filtered_words))

def match_data(ch_data, filtered_words):
    matched_data = pd.DataFrame()
    for column in ['陸1', '陸2', '陸3']:
        matched_rows = ch_data[ch_data[column].apply(lambda x: any(word in str(x) and len(word) > 1 for word in filtered_words))]
        matched_data = pd.concat([matched_data, matched_rows])
    return matched_data.drop_duplicates()

def generate_content(model, matched_data, prompt):
    matched_data_str = matched_data.to_string()
    response = model.generate_content('參考資料：' + matched_data_str + '\n\n指令：將以下文字中的大陸用語轉換為台灣用語。僅輸出轉換後的結果,不要加上任何解釋、前言或結語。\n\n範例：\n\n使用者輸入：在這個資訊爆炸的時代，我們經常需要從各種來源獲取信息。然而，這些信息的質量和可靠性卻常常讓人擔憂。因此，我們需要一種機制來評估和改進我們的信息來源，這就是「反饋的重要性。\n\n 模型輸出：在這個資訊爆炸的時代，我們經常需要從各種來源取得資訊。然而，這些資訊的品質和可靠性卻常常讓人擔憂。因此，我們需要一種機制來評估和改進我們的資訊來源，這就是回饋的重要性。    \n\n待轉換文字：' + prompt,
    safety_settings={
        'HATE': 'BLOCK_NONE',
        'HARASSMENT': 'BLOCK_NONE',
        'SEXUAL' : 'BLOCK_NONE',
        'DANGEROUS' : 'BLOCK_NONE'
    })
    return response.text

# 初始化全局變數
model = configure_genai('api_key.txt')
ch_data = load_data('ch.csv')

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    filtered_words = filter_words(user_message, nlp_zh)
    matched_data = match_data(ch_data, filtered_words)
    response_text = generate_content(model, matched_data, user_message)
    return jsonify({'response': response_text})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)