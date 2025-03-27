import os
import qrcode
import pandas as pd
from malevich.square import APP_DIR, DF, Context, processor, scheme
from pydantic import BaseModel
from datetime import datetime
from PIL import Image, ImageEnhance
from psd_tools import PSDImage

@scheme()
class UrlInput(BaseModel):
    url: str

@processor()
def generate_qr_code(data: DF[UrlInput], context: Context):
    """Generates a QR code for a URL and saves it as a PNG file.
    
    ## Input:
    A dataframe with a column:
    - `url` (str): URL to convert to QR code.
    
    ## Output:
    A dataframe with a column:
    - `qr_code_path` (str): Path to the generated QR code image.
    
    -----
    Args:
        data: A dataframe with a column named `url` containing URLs to convert.
        context: A context object.
        
    Returns:
        A dataframe with a column named `qr_code_path` containing paths to generated QR codes.
    """
    outputs = []
    
    for url in data.url.to_list():
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"qrcode_{timestamp}.png"
        
        # Save to app directory and share
        file_path = os.path.join(APP_DIR, filename)
        # file_path = os.path.join("./", filename)
        img.save(file_path)
        
        # Share the file
        context.share(filename)
        context.synchronize([filename])
        
        outputs.append(filename)
    
    # Return DataFrame with paths to QR code images
    return pd.DataFrame(outputs, columns=['qr_code'])

@scheme()
class ImageEnhancementInput(BaseModel):
    fileName: str
    contrast: float
    saturation: float

@processor()
def enhance_image(data: DF[ImageEnhancementInput], context: Context):
    """Enhances an image and saves it as a TIFF file.
    
    ## Input:
    A dataframe with 3 columns:
    - `fileName` (str): Name of the image file.
    - `contrast` (float): Contrast value.
    - `saturation` (float): Saturation value.
    
    ## Output:
    A dataframe with a column:
    - `enhanced_image` (str): Path to the enhanced image file.
    
    -----
    Args:
        data: A dataframe with 3 columns: `fileName`, `contrast`, `saturation`.
        context: A context object.
        
    Returns:
        A dataframe with a column named `enhanced_image_path` containing paths to enhanced image files.
    """
    outputs = []
    
    for fileName, contrast, saturation in data.to_dict(orient='records'):
        # Open file
        if fileName.lower().endswith('.psd'):
            psd = PSDImage.open(fileName)
            img = psd.composite().convert('RGBA')
        else:
            img = Image.open(fileName).convert("RGBA")  # Convert to RGBA to preserve transparency
        
        # Enhance contrast
        contrastImg = ImageEnhance.Contrast(img)
        img = contrastImg.enhance(contrast)  # Increase contrast

        # Enhance saturation
        saturationImg = ImageEnhance.Color(img) 
        img = saturationImg.enhance(saturation)  # Boost saturation
        
        # Generate output filename    # Save enhanced RGBA image
        filename = f"{filename}_enhanced.tiff"
        
        # Save to app directory and share
        file_path = os.path.join(APP_DIR, filename)
        img.save(file_path, "TIFF")
        
        # Share the file
        context.share(filename)
        context.synchronize([filename])
        
        outputs.append(filename)
    
    # Return DataFrame with paths to QR code images
    return pd.DataFrame(outputs, columns=['enhanced_image'])

@scheme()
class ImageFileInput(BaseModel):
    fileName: str

@processor()
def convert_to_cmyk(data: DF[ImageFileInput], context: Context):
    """Converts an image to CMYK and saves it as a TIFF file.
    
    ## Input:
    A dataframe with 1 column:
    - `fileName` (str): Name of the image file.
    
    ## Output:
    A dataframe with a column:
    - `cmyk_image` (str): Path to the CMYK image file.
    
    -----
    Args:
        data: A dataframe with 1 column: `fileName`.
        context: A context object.
        
    Returns:
        A dataframe with a column named `cmyk_image` containing paths to CMYK image files.
    """
    outputs = []
    
    for fileName in data.fileName.to_list():
        # Open file
        img = Image.open(fileName)
        
        # Extract alpha channel if present
        alpha = None
        if img.mode == 'RGBA':
            alpha = img.getchannel('A')
    
        # Convert to CMYK
        cmyk = img.convert("CMYK")
    
        # Save with alpha if it existed
        if alpha:
            cmyk.putalpha(alpha)
        
        # Generate output filename
        filename = f"{filename}_CMYK.tiff"
        
        # Save to app directory and share
        file_path = os.path.join(APP_DIR, filename)
        cmyk.save(file_path)
        
        # Share the file
        context.share(filename)
        context.synchronize([filename])
        
        outputs.append(filename)
    
    # Return DataFrame with paths to QR code images
    return pd.DataFrame(outputs, columns=['cmyk_image'])

@processor()
def extract_white_underbase(data: DF[ImageFileInput], context: Context):
    """Extracts a white underbase mask for printing on dark fabrics.
    
    ## Input:
    A dataframe with 1 column:
    - `fileName` (str): Name of the image file.
    
    ## Output:
    A dataframe with a column:
    - `underbase_image` (str): Path to the underbase image file.
    
    -----
    Args:
        data: A dataframe with 1 column: `fileName`.
        context: A context object.
        
    Returns:
        A dataframe with a column named `underbase_image` containing paths to underbase image files.
    """
    outputs = []
    
    for fileName in data.fileName.to_list():
        # Open image and ensure it's in RGBA mode
        img = Image.open(fileName).convert("RGBA")

        # Convert to grayscale (luminance)
        grayscale = img.convert("L")

        # Extract the alpha channel
        alpha = img.split()[3]  # The fourth channel in RGBA

        # Create the underbase, but retain transparency
        underbase = grayscale.point(lambda p: 255 if p < 200 else 0)

        # Apply transparency by combining with alpha channel
        underbase = Image.merge("LA", (underbase, alpha))  # "L" for grayscale, "A" for alpha

        # Convert back to RGBA (optional, if you need an RGBA output)
        underbase = underbase.convert("RGBA")

        # Generate output filename
        filename = f"{filename}_underbase.tiff"
        
        # Save to app directory and share
        file_path = os.path.join(APP_DIR, filename)
        underbase.save(file_path, "TIFF")

        # Share the file
        context.share(filename)
        context.synchronize([filename])
        
        outputs.append(filename)
    
    # Return DataFrame with paths to QR code images
    return pd.DataFrame(outputs, columns=['underbase_image'])

