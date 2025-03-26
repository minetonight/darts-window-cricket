# Android Build Documentation

## Font Handling

### Project Structure

For cross-platform compatibility, Aleks chose fastest option:

#### Option 1: Separate Font Directories (Recommended)
```
your_project/
├── assets/
│   └── fonts/          # Android fonts
└── fonts/              # Desktop fonts
```

### Configuration

1. Add fonts to your project in the `assets/fonts` directory
2. Configure buildozer.spec to include fonts:
```ini
# If using Option 1 (separate directories):
android.add_assets = assets/fonts
```

### Font Path Usage

When referencing fonts in your Kivy code (`.kv` files or Python), use the following path format:

```python
# Correct:
font_name: 'fonts/Roboto-Bold.ttf'

# Incorrect:
font_name: 'assets/fonts/Roboto-Bold.ttf'  # Don't include 'assets/'
```

### Why This Works

1. The `android.add_assets = assets/fonts` directive copies the contents of your local `assets/fonts` directory directly into the `assets` directory of the APK
2. When the app runs on Android, it looks for fonts relative to the `assets` directory
3. Therefore, we don't include `assets/` in the font path when referencing fonts in our code

### Common Issues

1. **Crash on Font Loading**: If the app crashes when trying to load fonts, check:
   - The font path in your code (should not include 'assets/')
   - The font files are actually included in the APK (check with `unzip -l your.apk | grep fonts`)
   - The font filenames match exactly (case-sensitive)

2. **Font Not Found**: If fonts aren't being found:
   - Verify the `android.add_assets` line in buildozer.spec
   - Clean and rebuild the APK:
     ```bash
     buildozer android clean
     buildozer android debug
     ```

### Best Practices

1. Keep font files in `assets/fonts` directory
2. Use consistent naming for font files
3. Test font loading on both development and release builds
4. Consider font file sizes for APK optimization 