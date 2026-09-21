"""
Upload news-monitor-agent project to MEGA cloud storage.
Requires MEGA email and password.
"""

from mega import Mega
import os
import zipfile
from datetime import datetime

def create_project_zip():
    """Create a zip file of the project."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    zip_name = f"news-monitor-agent-{datetime.now().strftime('%Y%m%d')}.zip"
    zip_path = os.path.join(project_dir, zip_name)
    
    # Exclude certain files/directories
    exclude = {'.git', '__pycache__', '.env', 'data', 'logs', '*.pyc', '.gitignore'}
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude and not d.startswith('.')]
            
            for file in files:
                if not file.endswith('.pyc') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
    
    return zip_path

def upload_to_mega(email, password):
    """Upload project zip to MEGA."""
    try:
        # Create zip file
        print("Creating project zip file...")
        zip_path = create_project_zip()
        print(f"✅ Created: {zip_path}")
        
        # Login to MEGA
        print(f"\nLogging in to MEGA as {email}...")
        m = Mega()
        m.login(email, password)
        print("✅ Successfully logged in to MEGA")
        
        # Upload file
        print(f"\nUploading {os.path.basename(zip_path)} to MEGA...")
        uploaded = m.upload(zip_path)
        print(f"✅ Successfully uploaded to MEGA")
        print(f"   File ID: {uploaded}")
        
        # Clean up local zip
        os.remove(zip_path)
        print(f"\n✅ Cleaned up local zip file")
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("MEGA Upload Script for News Monitor Agent")
    print("=" * 50)
    
    email = input("Enter your MEGA email: ")
    password = input("Enter your MEGA password: ")
    
    if upload_to_mega(email, password):
        print("\n✅ Upload completed successfully!")
    else:
        print("\n❌ Upload failed. Please check your credentials and try again.")
