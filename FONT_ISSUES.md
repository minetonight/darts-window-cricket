# Font Issues and Lessons Learned

## The Problem
The app was crashing on Android devices when trying to load custom fonts. This was particularly frustrating because:
1. The app worked perfectly on desktop
2. The fonts were properly included in the APK
3. The paths were correctly configured
4. The crash only happened on the game screen, not the data input screen

## Attempted Solutions

### 1. Font Directory Structure
Tried different approaches for font organization:
- Fonts in `assets/fonts/`
- Fonts in root `fonts/` directory
- Separate directories for desktop and Android

### 2. Buildozer Configuration
Attempted various buildozer.spec configurations:
```ini
# Tried these variations:
android.add_assets = assets/fonts
android.add_assets = fonts
```

### 3. Font Path Handling
Tried different path formats in the code:
- `'fonts/Roboto-Bold.ttf'`
- `'assets/fonts/Roboto-Bold.ttf'`
- Platform-specific paths using `kivy.utils.platform`

### 4. Font File Issues
The `CODE2000.ttf` font (7.5MB) was particularly problematic:
- Too large for mobile
- Caused crashes on Android
- Not necessary for basic functionality

## The Solution
Eventually gave up on custom fonts and simplified the approach:
1. Removed all custom font references
2. Using system default fonts
3. Using simple ASCII characters for marks and dots:
   ```python
   mark.text = 'V'  # Instead of check mark
   dots = 'v' * current_round_hits  # Instead of bullet points
   ```

## Lessons Learned
1. **Simplicity is Better**: Using system fonts and simple ASCII characters is more reliable than custom fonts
2. **Mobile Limitations**: Android has stricter limitations on font handling than desktop
3. **Testing is Crucial**: Always test on both desktop and mobile, as behavior can differ significantly

## Future Considerations
If custom fonts are needed in the future:
1. Test thoroughly on both platforms
 - dont use fonts again, or test every single tiny change on the phone.
2. Have a fallback to system fonts 