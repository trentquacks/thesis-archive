import os
from werkzeug.utils import secure_filename
from flask import current_app

# flaskr/utils.py
import os
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_file(file, subfolder, prefix="", allowed_extensions=None, max_size_mb=None):
    if not file or file.filename == '':
        return None, None, None

    filename = secure_filename(file.filename)

    if allowed_extensions:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed_extensions:
            raise ValueError(f"Invalid file type. Only {', '.join(allowed_extensions).upper()} files are allowed.")

    if max_size_mb:
        file.seek(0, os.SEEK_END)
        file_length = file.tell() # read size
        file.seek(0)  # reset stream position
        if file_length > max_size_mb * 1024 * 1024:
            raise ValueError(f"File is too large. Maximum size limit is {max_size_mb}MB.")

    if prefix:
        filename = f"{prefix}_{filename}"
        
    save_directory = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(save_directory, exist_ok=True)
    
    actual_save_path = os.path.join(save_directory, filename)
    file.save(actual_save_path)
    
    base_url = current_app.config['UPLOAD_URL']
    relative_web_path = f"{base_url}/{subfolder}/{filename}"
    
    return relative_web_path, actual_save_path, filename
