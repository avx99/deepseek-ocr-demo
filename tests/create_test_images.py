"""
Sample test images for testing OCR functionality
"""

import os
from PIL import Image, ImageDraw, ImageFont


def create_sample_images():
    """Create sample images for testing"""
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Sample 1: Simple text image
    create_simple_text_image(os.path.join(data_dir, 'simple_text.jpg'))
    
    # Sample 2: Document with multiple lines
    create_document_image(os.path.join(data_dir, 'document.jpg'))
    
    # Sample 3: Numbers and symbols
    create_numbers_image(os.path.join(data_dir, 'numbers.jpg'))
    
    # Sample 4: Mixed content
    create_mixed_content_image(os.path.join(data_dir, 'mixed.jpg'))
    
    # Sample 5: Low quality image
    create_low_quality_image(os.path.join(data_dir, 'low_quality.jpg'))
    
    print("Sample images created in tests/data/")


def create_simple_text_image(path):
    """Create simple text image"""
    image = Image.new('RGB', (400, 100), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        # Try to use a better font if available
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fall back to default font
        font = ImageFont.load_default()
    
    draw.text((20, 30), "Hello World!", fill='black', font=font)
    image.save(path, 'JPEG')


def create_document_image(path):
    """Create document-like image with multiple lines"""
    image = Image.new('RGB', (600, 400), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        title_font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
        title_font = font
    
    # Title
    draw.text((50, 30), "Sample Document", fill='black', font=title_font)
    
    # Content
    lines = [
        "This is a sample document for testing OCR functionality.",
        "It contains multiple lines of text with different content.",
        "The OCR system should be able to extract all this text",
        "accurately and maintain the structure of the document.",
        "",
        "Contact Information:",
        "Email: test@example.com",
        "Phone: (555) 123-4567",
        "Address: 123 Main St, Anytown, USA 12345"
    ]
    
    y_position = 80
    for line in lines:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 25
    
    image.save(path, 'JPEG')


def create_numbers_image(path):
    """Create image with numbers and symbols"""
    image = Image.new('RGB', (300, 200), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    numbers_text = [
        "Invoice #: INV-2024-001",
        "Amount: $1,234.56",
        "Date: 01/15/2024",
        "Tax: 8.25%",
        "Total: $1,336.12"
    ]
    
    y_position = 30
    for text in numbers_text:
        draw.text((20, y_position), text, fill='black', font=font)
        y_position += 30
    
    image.save(path, 'JPEG')


def create_mixed_content_image(path):
    """Create image with mixed content types"""
    image = Image.new('RGB', (500, 300), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Table-like structure
    draw.text((20, 20), "Product         Qty    Price", fill='black', font=font)
    draw.text((20, 40), "=====================================", fill='black', font=font)
    draw.text((20, 60), "Widget A        2      $25.00", fill='black', font=font)
    draw.text((20, 80), "Widget B        1      $15.50", fill='black', font=font)
    draw.text((20, 100), "Widget C        3      $8.75", fill='black', font=font)
    draw.text((20, 120), "=====================================", fill='black', font=font)
    draw.text((20, 140), "TOTAL                  $74.75", fill='black', font=font)
    
    # Add some shapes
    draw.rectangle([300, 50, 450, 150], outline='black', width=2)
    draw.text((310, 90), "PAID", fill='red', font=font)
    
    image.save(path, 'JPEG')


def create_low_quality_image(path):
    """Create low quality image to test OCR robustness"""
    # Create normal image first
    image = Image.new('RGB', (400, 150), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 50), "This text is hard to read", fill='gray', font=font)
    
    # Resize to make it blurry
    image = image.resize((100, 37))
    image = image.resize((400, 150))
    
    image.save(path, 'JPEG', quality=30)  # Low quality JPEG


def create_test_pdf():
    """Create a simple PDF for testing"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        pdf_path = os.path.join(data_dir, 'sample.pdf')
        
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add text to PDF
        c.drawString(100, height - 100, "Sample PDF Document")
        c.drawString(100, height - 130, "This is a test PDF file for OCR testing.")
        c.drawString(100, height - 160, "It contains multiple lines of text.")
        c.drawString(100, height - 190, "Email: sample@example.com")
        c.drawString(100, height - 220, "Phone: (555) 987-6543")
        
        c.save()
        print(f"Sample PDF created: {pdf_path}")
        
    except ImportError:
        print("ReportLab not available, skipping PDF creation")


if __name__ == '__main__':
    create_sample_images()
    create_test_pdf()