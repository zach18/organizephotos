"""
Organize pictures by Year/Month/Day while preserving date metadata for OneDrive's "This Day" feature.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import win32_setctime

def get_date_taken(image_path):
    """
    Extract the date taken from image EXIF data or fall back to file modification date.
    """
    try:
        # Try to get EXIF data
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal" or tag == "DateTime":
                    # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                    date_str = value
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"Could not read EXIF from {image_path}: {e}")
    
    # Fall back to file modification time
    timestamp = os.path.getmtime(image_path)
    return datetime.fromtimestamp(timestamp)

def organize_pictures(source_dir=None, dry_run=False):
    """
    Organize pictures into Year/Month/Day folder structure.
    
    Args:
        source_dir: Path to Pictures directory (default: user's Pictures folder)
        dry_run: If True, only show what would be done without copying files
    """
    if source_dir is None:
        source_dir = Path.home() / "Pictures"
    else:
        source_dir = Path(source_dir)
    
    if not source_dir.exists():
        print(f"Directory not found: {source_dir}")
        return
    
    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw'}
    
    # Get all image files recursively from all subdirectories
    image_files = [f for f in source_dir.rglob('*') 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    print(f"Found {len(image_files)} image files in {source_dir}")
    
    moved_count = 0
    error_count = 0
    
    for image_file in image_files:
        try:
            # Get the date the picture was taken
            date_taken = get_date_taken(image_file)
            
            # Create folder structure: Year/Month/Day (e.g., "2024/01/15")
            year = date_taken.strftime("%Y")
            month = date_taken.strftime("%m")
            day = date_taken.strftime("%d")
            
            target_folder = source_dir / year / month / day
            target_path = target_folder / image_file.name
            
            # Check if file already exists in target location and create unique name if needed
            if target_path.exists():
                # Append "-copy" to the filename before the extension
                stem = image_file.stem
                suffix = image_file.suffix
                counter = 1
                new_name = f"{stem}-copy{suffix}"
                target_path = target_folder / new_name
                
                # If that also exists, add numbers: -copy2, -copy3, etc.
                while target_path.exists():
                    counter += 1
                    new_name = f"{stem}-copy{counter}{suffix}"
                    target_path = target_folder / new_name
                
                print(f"⚠️  Duplicate found for {image_file.name} - saving as {new_name}")
            
            if dry_run:
                print(f"Would move: {image_file.name} -> {year}/{month}/{day}/")
            else:
                # Create target folder
                target_folder.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(image_file), str(target_path))
                
                # Set all timestamps to the date taken
                date_taken_timestamp = date_taken.timestamp()
                os.utime(target_path, (date_taken_timestamp, date_taken_timestamp))
                win32_setctime.setctime(str(target_path), date_taken_timestamp)
                
                print(f"✓ Moved: {image_file.name} -> {year}/{month}/{day}/ (Date: {date_taken.strftime('%Y-%m-%d')})")
                moved_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {image_file.name}: {e}")
            error_count += 1
    
    print(f"\n{'=' * 50}")
    print(f"Summary:")
    print(f"  Total images found: {len(image_files)}")
    print(f"  Successfully moved: {moved_count}")
    print(f"  Errors: {error_count}")
    print(f"  Skipped: {len(image_files) - moved_count - error_count}")

if __name__ == "__main__":
    import sys
    
    print("Picture Organization Tool")
    print("=" * 50)
    print("This will organize pictures into Year/Month/Day folders")
    print("while preserving all date metadata for OneDrive.\n")
    
    # First, do a dry run to show what will happen
    print("Running DRY RUN first to preview changes...\n")
    organize_pictures(dry_run=True)
    
    print("\n" + "=" * 50)
    response = input("\nProceed with moving files? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\nOrganizing pictures...\n")
        organize_pictures(dry_run=False)
        print("\n✓ Done! Your pictures are now organized by year, month, and day.")
    else:
        print("\nOperation cancelled.")
