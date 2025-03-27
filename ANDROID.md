# Android Build Documentation

## Font Handling

1. Add fonts to your project in the `assets/fonts` directory
2. Configure buildozer.spec to include fonts:
```ini
# Include font files in the build
source.include_exts = py,png,jpg,kv,atlas,ttf

```

### Font Path Usage

When referencing fonts in your Kivy code (`.kv` files or Python), use the following path format:

```python
# Correct:
font_name: 'assets/fonts/[fontname].ttf'  # For Android builds
```

### Why This Works

1. The `source.include_exts` directive ensures font files are included in the build


### Best Practices

1. Keep font files in `assets/fonts` directory for Android builds
2. Use consistent naming for font files
3. Test to make sure the fonts are loaded in the APK