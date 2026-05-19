import os
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_file(file, subfolder, prefix=""):
    if not file or file.filename == '':
        return None, None, None

    filename = secure_filename(file.filename)
    if prefix:
        filename = f"{prefix}_{filename}"
        
    save_directory = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
    os.makedirs(save_directory, exist_ok=True)
    
    actual_save_path = os.path.join(save_directory, filename)
    file.save(actual_save_path)
    
    relative_web_path = f"/static/uploads/{subfolder}/{filename}"
    
    return relative_web_path, actual_save_path, filename
