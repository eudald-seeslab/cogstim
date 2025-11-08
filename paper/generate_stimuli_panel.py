"""Generate a scientific journal ready panel of stimuli examples."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import string

def create_stimuli_panel(input_dir, output_file, ncols=4, cell_size=400, 
                         padding=20, label_size=60):
    """
    Create a panel figure with all stimuli images labeled with lowercase letters.
    
    Parameters
    ----------
    input_dir : str or Path
        Directory containing the stimulus images
    output_file : str or Path
        Output file path for the panel PNG
    ncols : int
        Number of columns in the panel grid
    cell_size : int
        Size of each cell in pixels
    padding : int
        Padding between cells in pixels
    label_size : int
        Font size for labels
    """
    input_path = Path(input_dir)
    
    # Get all PNG files and sort them alphabetically
    image_files = sorted(input_path.glob("*.png"))
    
    
    n_images = len(image_files)
    nrows = (n_images + ncols - 1) // ncols  # Calculate rows needed
    
    # Calculate panel dimensions
    panel_width = ncols * cell_size + (ncols + 1) * padding
    panel_height = nrows * cell_size + (nrows + 1) * padding
    
    # Create white background
    panel = Image.new('RGB', (panel_width, panel_height), 'white')
    draw = ImageDraw.Draw(panel)
    
    # Try to load a nice font, try multiple common paths
    font_paths = [
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
        "/usr/share/fonts/open-sans/OpenSans-Bold.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSans-Bold.ttf",
    ]
    
    font = None
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, label_size)
            print(f"Loaded font: {font_path} at size {label_size}")
            break
        except:
            continue
    
    if font is None:
        print(f"WARNING: Could not load TrueType font, using default (size parameter ignored)")
        font = ImageFont.load_default()
    
    # Place each image
    for idx, img_file in enumerate(image_files):
        row = idx // ncols
        col = idx % ncols
        
        # Calculate position
        x = col * cell_size + (col + 1) * padding
        y = row * cell_size + (row + 1) * padding
        
        # Load and resize image to fit cell
        img = Image.open(img_file)
        img = img.convert('RGBA')
        
        # Resize maintaining aspect ratio
        img.thumbnail((cell_size, cell_size), Image.Resampling.LANCZOS)
        
        # Center image in cell
        img_x = x + (cell_size - img.width) // 2
        img_y = y + (cell_size - img.height) // 2
        
        # Paste image onto panel
        if img.mode == 'RGBA':
            panel.paste(img, (img_x, img_y), img)
        else:
            panel.paste(img, (img_x, img_y))
        
        # Add lowercase letter label
        label = string.ascii_lowercase[idx]
        
        label_x = x + 15
        label_y = y
        
        # Set label color: white for all except the last one (black)
        label_color = 'black' if idx == n_images - 1 else 'white'
        
        # Draw text without background rectangle
        draw.text((label_x, label_y), label, fill=label_color, font=font)
    
    # Save panel
    panel.save(output_file, dpi=(300, 300))
    print(f"Panel saved to: {output_file}")
    print(f"Dimensions: {panel_width} x {panel_height} pixels")
    print(f"Number of stimuli: {n_images}")

if __name__ == "__main__":
    input_dir = Path(__file__).parent / "assets" / "examples"
    output_file = Path(__file__).parent / "stimuli_panel.png"
    
    create_stimuli_panel(input_dir, output_file, ncols=4)
