# Give Space

**A mobile application that allows one device (Mobile A) to request and utilize the storage space of another device (Mobile B) over a network.**

Built with [Kivy](https://kivy.org/) and [KivyMD](https://kivymd.readthedocs.io/) for Android (API 21+).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [How It Works](#how-it-works)
4. [Prerequisites](#prerequisites)
5. [Setup for Development (Desktop)](#setup-for-development-desktop)
6. [Building for Android](#building-for-android)
7. [Deployment](#deployment)
8. [Configuration](#configuration)
9. [Data Privacy](#data-privacy)
10. [Troubleshooting](#troubleshooting)
11. [License](#license)

---

## Architecture Overview

```
┌─────────────────────────┐          ┌─────────────────────────┐
│       Mobile A          │          │       Mobile B          │
│   (Storage Consumer)    │          │   (Storage Provider)    │
│                         │          │                         │
│  ┌───────────────────┐  │  TCP/IP  │  ┌───────────────────┐  │
│  │   FileClient      │◄─┼──────────┼─►│   FileServer      │  │
│  │   (TCP Client)    │  │  JSON    │  │   (TCP Server)    │  │
│  └───────────────────┘  │  Protocol│  └───────────────────┘  │
│                         │          │                         │
│  ┌───────────────────┐  │          │  ┌───────────────────┐  │
│  │   FileCipher      │  │          │  │   StorageManager  │  │
│  │   (AES-256-GCM)   │  │          │  │   (Quota Mgmt)    │  │
│  └───────────────────┘  │          │  └───────────────────┘  │
│                         │          │                         │
│  ┌───────────────────┐  │          │  ┌───────────────────┐  │
│  │   File Manager UI │  │          │  │   MemorySync      │  │
│  │   (Home Screen)   │  │          │  │   (Auto-Update)   │  │
│  └───────────────────┘  │          │  └───────────────────┘  │
└─────────────────────────┘          └─────────────────────────┘
```

### Key Components

| Component | Description |
|-----------|-------------|
| **FileClient** | TCP client on Mobile A that sends file operation requests |
| **FileServer** | TCP server on Mobile B that processes file requests |
| **MessageProtocol** | Length-prefixed JSON protocol for all network messages |
| **StorageManager** | Quota-aware filesystem wrapper on Mobile B |
| **FileCipher** | AES-256-GCM encryption for "Hide" privacy mode |
| **MemorySync** | Auto-detects network changes and syncs storage stats |
| **PairingManager** | Handles 4-digit code pairing and device persistence |

### Network Protocol

All communication uses a simple length-prefixed JSON format:

```
[4-byte uint32 payload length (big-endian)][JSON payload]
```

Message types cover: directory listing, file upload, download, delete, rename, stats, and pairing.

---

## Project Structure

```
GiveSpace/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── buildozer.spec               # Android build configuration
├── README.md                    # This file
│
├── src/                         # Python source code
│   ├── app.py                   # KivyMD Application class
│   │
│   ├── screens/                 # UI screen modules
│   │   ├── splash_screen.py     # "M.S.U" splash screen
│   │   ├── role_screen.py       # Role selection (A or B)
│   │   ├── pairing_screen.py    # 4-digit pairing code
│   │   ├── home_screen.py       # File manager / Dashboard
│   │   └── settings_screen.py   # Settings & server config
│   │
│   ├── network/                 # Network layer
│   │   ├── protocol.py          # Message protocol (JSON + length prefix)
│   │   ├── pairing.py           # 4-digit code generation & verification
│   │   ├── server.py            # TCP file server (Mobile B)
│   │   └── client.py            # TCP file client (Mobile A)
│   │
│   ├── storage/                 # Storage management
│   │   ├── manager.py           # Quota enforcement & file ops
│   │   └── sync.py              # Network-aware memory sync
│   │
│   └── encryption/              # Privacy & encryption
│       └── crypto.py            # AES-256-GCM file encryption
│
├── kv/                          # Kivy Language UI definitions
│   ├── splash.kv
│   ├── role.kv
│   ├── pairing.kv
│   ├── home.kv
│   └── settings.kv
│
└── icon/                        # App icon assets
    └── icon_spec.md             # Icon design specification
```

---

## How It Works

### 1. First Run — Role Selection

- **Mobile B** (Storage Provider): Select "I am Mobile B"
  - Goes to Settings → Configures storage allocation → Starts server
  - Server displays a 4-digit code and its IP address

- **Mobile A** (Storage Consumer): Select "I am Mobile A"
  - Goes to Pairing screen → Enters Mobile B's IP and 4-digit code
  - Connection established

### 2. Pairing

- Mobile B generates a random 4-digit code
- Mobile A enters the code + Mobile B's IP address
- On success: devices are paired and the pairing info is saved locally
- On failure: error dialog with details

### 3. File Operations

Once paired, Mobile A can:
- **Browse** remote directories (with navigation)
- **Upload** files (with optional encryption in "Hide" mode)
- **Download** files from remote storage
- **Delete** files on remote storage
- **Create** directories

### 4. Hide/Unhide (Data Privacy)

Toggle the switch in Mobile A's file manager:
- **Hide ON**: Files are encrypted with AES-256-GCM before upload
- **Hide OFF**: Files are transferred in plain text

### 5. Memory Sync

When Mobile B connects to a network, the `MemorySync` module:
1. Detects the network state change
2. Recalculates storage usage stats
3. Broadcasts updated stats to all connected Mobile A devices

---

## Prerequisites

### For Development (Desktop)
- Python 3.8+
- pip

### For Android Build
- Linux or WSL2 (Windows Subsystem for Linux)
- Python 3.8+
- Buildozer (`pip install buildozer`)
- Android SDK & NDK (installed automatically by Buildozer)
- Java JDK 11+

### For Windows Desktop Testing
- Python 3.8+ (Python 3.13 confirmed working)
- Kivy 2.3.x
- KivyMD 2.0.x
- Windows 10+

---

## Setup for Development (Desktop)

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/yourusername/GiveSpace.git
cd GiveSpace

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run the App

```bash
python main.py
```

This will launch the desktop window at 400×720px (phone-like dimensions).

### 3. Desktop Testing Workflow

For testing both roles on a single machine:
1. Run the app once → Select Mobile B → Start server in Settings
2. Run the app again (second instance) → Select Mobile A → Enter `127.0.0.1` as IP + the displayed code

---

## Building for Android

### Method 1: Using Buildozer (Recommended)

#### On Linux (or WSL2):

```bash
# Install Buildozer dependencies
sudo apt update
sudo apt install -y \
    python3-pip \
    build-essential \
    git \
    python3-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libopenal-dev

# Install Buildozer
pip install --user buildozer

# Build the APK
cd /path/to/GiveSpace
buildozer android debug
```

The APK will be generated at:
```
bin/GiveSpace-1.0.0-<arch>-debug.apk
```

#### Build Options

```bash
# Clean build
buildozer android clean
buildozer android debug

# Deploy to connected device
buildozer android debug deploy run

# Release build (requires keystore)
buildozer android release
```

### Method 2: Using python-for-android (Manual)

```bash
pip install python-for-android

p4a apk \
    --private . \
    --package org.givespace.givspace \
    --name "Give Space" \
    --version 1.0.0 \
    --bootstrap sdl2 \
    --requirements python3,kivy==2.3.1,kivymd,cryptography>=41.0.0,netifaces>=0.11.0 \
    --arch arm64-v8a \
    --arch armeabi-v7a \
    --permission INTERNET \
    --permission ACCESS_WIFI_STATE \
    --permission ACCESS_NETWORK_STATE \
    --min-sdk 21 \
    --target-sdk 34 \
    --enable-androidx
```

---

## Deployment

### Manual Install

1. Copy `bin/GiveSpace-1.0.0-arm64-v8a-debug.apk` to your Android device
2. Enable **Install from Unknown Sources** in Settings
3. Tap the APK file to install

### Using ADB (Debug)

```bash
# Connect device via USB with debugging enabled
buildozer android debug deploy run

# Or manually:
adb install -r bin/GiveSpace-1.0.0-arm64-v8a-debug.apk
```

---

## Configuration

### Storage Allocation (Mobile B)

Configure in **Settings** screen:
- **Slider**: 128 MB to 32 GB
- **Default**: 1024 MB (1 GB)
- Changes apply immediately when "Apply Allocation" is pressed
- Preferences persist across app restarts

### Server Port

Default: **9876**

The server binds to `0.0.0.0:9876` on Mobile B. Mobile A connects to `<MobileB_IP>:9876`.

### Paired Devices

Paired devices are stored in `paired_devices.json` in the app's working directory.
- View paired devices in Mobile A's Settings
- Unpair devices by tapping "Unpair"

---

## Data Privacy

### Hide Mode (AES-256-GCM Encryption)

When **Hide** is toggled ON in Mobile A's file manager:

1. **Before upload**: The file is encrypted using AES-256-GCM
   - A random 16-byte salt is generated
   - A 256-bit key is derived via PBKDF2 (100,000 iterations, SHA-256)
   - A 12-byte nonce is generated
   - The file is encrypted and authenticated

2. **Transfer**: Encrypted file + `.hidden` suffix is sent

3. **On Mobile B**: The encrypted file is stored as-is — decryption requires
   the same password (currently derived from the default pairing key)

### Security Notes

- Encryption is **not enabled by default** — user must toggle it on
- The cipher uses PBKDF2 key derivation to resist brute force
- The `.hidden` suffix prevents accidental double-encryption
- For production use, replace the default password with the actual pairing code

---

## Troubleshooting

### App Crashes on Startup

```bash
# Run with debug logging
python main.py --log-level DEBUG

# Check if KivyMD is installed
pip show kivymd
```

### Connection Issues

1. **Both devices must be on the same network** (same Wi-Fi)
2. Check firewall settings — port 9876 must be open
3. Verify IP address: both devices should show IPs in the same subnet
4. Try pinging Mobile B's IP from Mobile A

### Buildozer Errors

```bash
# Check Buildozer logs
buildozer android debug 2>&1 | tail -50

# Known issues:
# - "No module named 'buildozer'": pip install buildozer
# - SDK/NDK download failures: Use --local option or pre-install Android SDK
# - Java version mismatch: Install JDK 11 (java --version)
```

### Permission Issues (Android 11+)

Android 11+ scoped storage may affect file operations. The app uses:
- `INTERNET` — for TCP communication
- `ACCESS_WIFI_STATE` — for network detection
- `ACCESS_NETWORK_STATE` — for connectivity checks

---

## Technical Details

### Minimum Requirements

- **Android**: API level 21 (Android 5.0)
- **Network**: Wi-Fi (both devices on same LAN)
- **Storage**: 50 MB for the app + allocated storage space

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| kivy | 2.3.1 | Cross-platform GUI framework |
| kivymd | 2.0+ | Material Design components |
| cryptography | 41.0+ | AES-256-GCM encryption |
| netifaces | 0.11+ | Network interface detection |

### Buildozer Spec Highlights

- `android.api = 34` (Android 14 target)
- `android.minapi = 21` (Android 5.0 minimum)
- `android.archs = arm64-v8a, armeabi-v7a`
- `android.permissions = INTERNET, ACCESS_WIFI_STATE, ACCESS_NETWORK_STATE`

---

## License

This project is provided for educational and demonstration purposes.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

*Give Space — Share storage, not limits.*