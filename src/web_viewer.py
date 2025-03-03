from typing import Dict, List

from bson.objectid import ObjectId
from flask import Flask, jsonify, render_template

from mongodb_read_data import concate_ancestor_entries_unit_number
from utils.mongodb import get_database

app = Flask(__name__)


def get_regulation_content(regulation_title: str) -> Dict:
    """獲取法規內容及其結構

    Args:
        regulation_title: 法規名稱

    Returns:
        Dict: {
            'meta_data': str,  # 法規前言資料
            'entries': List[Dict],  # 法規條文內容及結構
        }
    """
    db = get_database()

    # 獲取法規基本資料
    regulations_collection = db['regulations']
    regulation = regulations_collection.find_one({'title': regulation_title})

    # 獲取所有條文
    entries_collection = db['entries']
    entries = entries_collection.find({'ref_regulation': regulation['_id']})

    return {'meta_data': regulation['meta_data'], 'entries': list(entries)}


@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')


@app.route('/regulation/<title>')
def show_regulation(title: str):
    """顯示特定法規內容頁面"""
    content = get_regulation_content(title)
    return render_template('regulation.html', content=content)


@app.route('/api/hierarchy/<entry_id>')
def get_hierarchy(entry_id: str):
    """API: 獲取特定條文的完整階層路徑"""

    hierarchy_path = concate_ancestor_entries_unit_number(ObjectId(entry_id))

    return jsonify({'hierarchy': ' '.join(hierarchy_path)})


if __name__ == '__main__':
    app.run(debug=True)
