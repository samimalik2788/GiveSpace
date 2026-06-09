# Give Space — App Icon Specification

## Design Requirements

- **Theme**: 70% Green (left) / 30% White (right) split
- **Style**: Modern, flat Material Design 3
- **Format**: 1024×1024 px PNG (base for all platform sizes)

## Color Palette

| Element   | Color Code | Description              |
|-----------|------------|--------------------------|
| Left side | `#4CAF50`  | Material Green 500       |
| Right side| `#FFFFFF`  | Pure white               |
| Accent    | `#2E7D32`  | Dark green (icon detail) |

## Composition

```
┌──────────────────┬──────────────┐
│                  │              │
│    GREEN         │    WHITE     │
│    (#4CAF50)     │    (#FFFFFF) │
│    70% width     │   30% width  │
│                  │              │
│    [SD Card]     │    [Wi-Fi]   │
│    Icon in       │    Icon in   │
│    white         │    dark      │
│                  │              │
└──────────────────┴──────────────┘
```

## Detailed Layout

1. **Background**: Vertical split
   - Left 70%: Solid `#4CAF50` (Material Green 500)
   - Right 30%: Solid `#FFFFFF` (White)

2. **Left side (Green)**:
   - A white SD card / storage chip icon (centered vertically)
   - Icon size: ~40% of the left area
   - Stroke width: 4px, filled outline style
   - Slightly offset right to balance the composition

3. **Right side (White)**:
   - A dark green (`#2E7D32`) Wi-Fi signal icon (centered vertically)
   - Icon size: ~40% of the right area
   - Stroke width: 4px, filled outline style

4. **Optional bottom bar**:
   - A thin (2px) accent line in dark green (`#2E7D32`) at the very bottom
   - Spans the full width of the icon

## Android Adaptive Icon

### Foreground (for API 26+)
```
File: icon/ic_foreground.png (108×108 dp)
- Same design as above, but cropped to safe zone
- No background color — leave transparent
```

### Background
```
File: icon/ic_background.png (108×108 dp)
- Solid #4CAF50 (use the green as the adaptive background)
```

### Legacy Icon
```
File: icon/app_icon.png (512×512 px)
- Full design as specified above
- Used for Android < API 26 and as fallback
```

## Generation Tools

Use any of these tools to create the icon:

1. **Canva**: Search "app icon template", apply split background
2. **Inkscape** (free): Create SVG with two rectangles + icon shapes
3. **Adobe Illustrator**: Same approach, export as PNG
4. **Android Studio**: Built-in Image Asset Studio for adaptive icons

## Buildozer Integration

In `buildozer.spec`, set:

```ini
icon.filename = %(source.dir)s/icon/app_icon.png
presplash.filename = %(source.dir)s/icon/presplash.png
```

## Delivery Notes

- Include all three files in the `icon/` directory:
  1. `app_icon.png` (512×512) — Primary app icon
  2. `ic_foreground.png` (108×108 dp) — Adaptive foreground
  3. `ic_background.png` (108×108 dp) — Adaptive background
  4. `presplash.png` (320×480) — Loading screen background (optional)