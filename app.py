from flask import Flask, request, jsonify, render_template, send_from_directory, session
import os
import json
from pathlib import Path
import io
import sys
import uuid
import secrets
import shutil

# Import kiro_renderer
try:
    import kiro_renderer
except ImportError:
    # If in the same directory
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import kiro_renderer

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = secrets.token_hex(16)  # Required for sessions

# Create storage directory if it doesn't exist
STORAGE_DIR = Path('kiro_files')
STORAGE_DIR.mkdir(exist_ok=True)

# Welcome template file path
WELCOME_TEMPLATE = STORAGE_DIR / 'welcome.kiro'

def get_user_dir():
    """Get or create user session directory"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_dir = STORAGE_DIR / session['user_id']
    if not user_dir.exists():
        user_dir.mkdir(parents=True, exist_ok=True)
        # Create welcome file for new users
        welcome_file = user_dir / 'welcome.kiro'
        if WELCOME_TEMPLATE.exists():
            # Read from template with utf-8 encoding and write to user file
            welcome_content = WELCOME_TEMPLATE.read_text(encoding='utf-8')
            welcome_file.write_text(welcome_content, encoding='utf-8')
        else:
            # Fallback content if template doesn't exist
            welcome_content = """# 환영합니다!

안녕하세요! KIRO 편집기에 오신 것을 환영합니다.

## 주요 기능
- 마크다운 스타일 편집
- 실시간 미리보기
- 파일 관리

새로운 문서를 작성하거나 이 문서를 수정해보세요."""
            welcome_file.write_text(welcome_content, encoding='utf-8')
    
    return user_dir

@app.route('/')
def index():
    # Ensure user directory exists and welcome file is created
    get_user_dir()
    return send_from_directory('.', 'index.html')

@app.route('/api/files')
def list_files():
    """Get the file structure for the current user"""
    result = []
    
    def traverse_dir(path, parent_id=None):
        items = []
        for item in path.iterdir():
            item_type = 'folder' if item.is_dir() else 'file'
            item_id = f"{parent_id}/{item.name}" if parent_id else item.name
            
            if item_type == 'folder':
                children = traverse_dir(item, item_id)
                items.append({
                    'id': item_id,
                    'name': item.name,
                    'type': item_type,
                    'children': children
                })
            else:
                if item.suffix == '.kiro':
                    items.append({
                        'id': item_id,
                        'name': item.name,
                        'type': item_type
                    })
        
        return sorted(items, key=lambda x: (x['type'] != 'folder', x['name']))
    
    try:
        user_dir = get_user_dir()
        result = traverse_dir(user_dir)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify(result)

@app.route('/api/file', methods=['GET'])
def get_file():
    """Get file content"""
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    try:
        user_dir = get_user_dir()
        full_path = user_dir / file_path
        content = full_path.read_text(encoding='utf-8')
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file', methods=['POST'])
def save_file():
    """Save file content"""
    data = request.json
    file_path = data.get('path')
    content = data.get('content', '')
    
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    try:
        user_dir = get_user_dir()
        full_path = user_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file', methods=['DELETE'])
def delete_file():
    """Delete a file or folder"""
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    try:
        user_dir = get_user_dir()
        full_path = user_dir / file_path
        if full_path.is_dir():
            import shutil
            shutil.rmtree(full_path)
        else:
            full_path.unlink()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/folder', methods=['POST'])
def create_folder():
    """Create a new folder"""
    data = request.json
    folder_path = data.get('path')
    
    if not folder_path:
        return jsonify({'error': 'No folder path provided'}), 400
    
    try:
        user_dir = get_user_dir()
        full_path = user_dir / folder_path
        full_path.mkdir(parents=True, exist_ok=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/render', methods=['POST'])
def render_kiro():
    """Render Kiro content to full HTML for iframe"""
    data = request.json
    content = data.get('content', '')

    if not content:
        return jsonify({'html': ''})

    try:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        html_body, global_class_str = kiro_renderer.render_kiro(content)
        sys.stdout = old_stdout

        font_styles = kiro_renderer.generate_font_styles()
        font_css = "\n".join([
            font_styles.get("google_fonts", ""),
            font_styles.get("custom_fonts_links", ""),
            f"<style>{font_styles.get('custom_fonts', '')}</style>"
        ])

        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>미리보기</title>
            <script src="https://cdn.tailwindcss.com"></script>
            {font_css}
        </head>
        <body class="bg-white">
            <article class="prose prose-lg max-w-screen-md px-6 mx-auto {global_class_str}">
                {html_body}
            </article>
        </body>
        </html>
        """

        return jsonify({'html': full_html.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 