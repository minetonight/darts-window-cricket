from PIL import Image, ImageDraw
import os

def create_icon(size=512):
    # Create foreground icon (dartboard)
    fg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(fg)
    
    # Draw dartboard
    center = size // 2
    radius = size // 2 - 20
    
    # Draw outer circle
    draw.ellipse([center - radius, center - radius, center + radius, center + radius], 
                 outline=(255, 255, 255), width=10)
    
    # Draw inner circles
    for r in [radius * 0.8, radius * 0.6, radius * 0.4, radius * 0.2]:
        draw.ellipse([center - r, center - r, center + r, center + r], 
                    outline=(255, 255, 255), width=5)
    
    # Draw crosshair
    draw.line([center - radius, center, center + radius, center], 
              fill=(255, 255, 255), width=5)
    draw.line([center, center - radius, center, center + radius], 
              fill=(255, 255, 255), width=5)
    
    # Create background icon (solid color)
    bg = Image.new('RGBA', (size, size), (41, 128, 185, 255))  # Nice blue color
    
    # Save icons
    fg.save('icon_fg.png')
    bg.save('icon_bg.png')
    
    # Create regular icon (combination of fg and bg)
    regular = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    regular.paste(bg, (0, 0))
    regular.paste(fg, (0, 0), fg)
    regular.save('icon.png')

if __name__ == '__main__':
    create_icon() 