"""
Buildozer Specification File for Give Space
============================================
Build command: buildozer android debug
Deploy command: buildozer android debug deploy run
"""

[app]

# (str) Title of your application
title = Give Space

# (str) Package name (must follow Android naming conventions)
package.name = givspace

# (str) Package domain (used as namespace)
package.domain = org.givespace

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to exclude (regular expressions)
source.exclude_exts = spec,pyc,pyo,png,jpg,jpeg,gif,db
source.exclude_dirs = tests, venv, .env, __pycache__, .git, .idea

# (list) List of custom source dirs to include
source.include_exts = py,png,jpg,kv,ttf,atlas

# (list) Application requirements
# Kivy 2.3.1, KivyMD, cryptography for AES-256 encryption, netifaces for IP detection
requirements = python3,kivy==2.3.1,kivymd,cryptography>=41.0.0,netifaces>=0.11.0,hostpython3

# (str) Custom source folders for requirements
# requirements.source.kivy = /path/to/kivy

# (str) Presplash of the application (image file)
# presplash.filename = %(source.dir)s/icon/presplash.png

# (str) Icon of the application (image file)
# icon.filename = %(source.dir)s/icon/app_icon.png

# (str) The orientation of the application
orientation = portrait

# (list) List of services to start
# services = SERVICE_NAME:ENTRY_POINT

# (bool) Indicate if the application is fullscreen
fullscreen = 1

# (bool) Indicate if the application uses a third-party cookie jar
# android.cookie_jar = False

# (bool) Enable android permissions
android.permissions = INTERNET, ACCESS_WIFI_STATE, ACCESS_NETWORK_STATE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# (list) Android extra API dependencies
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34

# (str) Android NDK directory (if not using Android SDK manager)
# android.ndk_path = 

# (str) Android SDK directory (if not using Android SDK manager)
# android.sdk_path = 

# (str) ANT directory (if not using Android SDK manager)
# android.ant_path =

# (bool) If True, then skip trying to update the Android SDK
# android.accept_sdk_license = True

# (bool) If True, then build in debug mode
android.debug = 0

# (str) Android logcat filter
android.logcat_filters = *:S python:D

# (bool) Copy the APK to the current directory
android.copy_libs = 1

# (str) Android architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (int) Android NDK API level
android.ndk_api = 21

# (bool) Use Android SDK, if True
android.sdk = 34

# (str) The Android Java SDK version
android.java_sdk_version = 11

# (bool) Enable targeting of Android 12+
android.enable_androidx = True

# (int) Android app min SDK version
android.min_sdk_version = 21

# (int) Android app target SDK version
android.target_sdk_version = 34

# (str) Android app theme
# android.app_theme = @android:style/Theme.Material.Light.NoActionBar

# (bool) If True, then build with gstreamer support
# android.gstreamer = False

# (bool) Enable gstreamer debug
# android.gstreamer_debug = False

# (str) The Android app entry point
android.entrypoint = main.py

# (str) The Android app permissions
android.add_permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE

# (list) Android add to manifest
android.manifest.add_activity = android:supportsRtl="true"

# (str) The Android app category
# android.category = 

# (str) The Android app ID
# android.app_id = 

# (list) Gradle dependencies to add
android.gradle_dependencies = 

# (list) Add aar libraries
# android.add_aars = 

# (list) Add jar libraries
# android.add_jars = 

# (list) Add custom build steps
# android.add_src = 

# (str) The Android app version code
android.version_code = 1

# (str) The Android app version name
android.version_name = 1.0.0

# (str) The Android app store
# android.store = 

# (str) The Android app store key
# android.store.key = 

# (str) The Android app store key alias
# android.store.key.alias = 

# (str) Path to the Android keystore
# android.keystore =

# (str) The Android app store password
# android.store.password = 

# (str) The Android app store key password
# android.store.key.password = 

# (bool) If True, then signs the APK with the debug key
android.debug_mode = 1

# (bool) If True, then the APK is signed with the release key
android.release_mode = 0

# (bool) If True, then the APK is signed with p4a key
# android.p4a_key = 

# (list) Android add to manifest
android.add_manifest_activity_metadata = 

# (str) Android extra XML manifest
# android.extra_manifest_xml = 

# (str) Android manifest placeholder
# android.manifest_placeholder = 

# (str) Android res directory
# android.res_dir = 

# (str) Android public libraries
# android.public_libs = 

# (str) Android private libraries
# android.private_libs = 

# (str) Android service
# android.service = 

# (str) Android service name
# android.service_name = 

# (str) Android service entry point
# android.service_entry = 

# (str) Android service foreground
# android.service_foreground = 

# (str) Android service icon
# android.service_icon = 

# (str) Android service permission
# android.service_permission = 

# (str) Android service process
# android.service_process = 

# (str) Android service task
# android.service_task = 

# (str) Android service label
# android.service_label = 

# (list) Android add to manifest activities
# android.add_manifest_activities = 

# (list) Android add to manifest services
# android.add_manifest_services = 

# (list) Android add to manifest receivers
# android.add_manifest_receivers = 

# (list) Android add to manifest providers
# android.add_manifest_providers = 

# (str) Android app label
# android.app_label = 

# (str) iOS app icon
# ios.app_icon = 

# (str) iOS app icon is precomposed
# ios.app_icon_is_precomposed = 

# (str) iOS app icon is prerendered
# ios.app_icon_is_prerendered = 

# (str) iOS app icon is prerendered for ipad
# ios.app_icon_prerendered_ipad = 

# (str) iOS app icon is prerendered for iphone
# ios.app_icon_prerendered_iphone = 

# (str) iOS app icon is prerendered for ipod
# ios.app_icon_prerendered_ipod = 

# (str) iOS app category
# ios.category = 

# (str) iOS app requires the device to have a camera
# ios.requires_camera = 

# (str) iOS app requires the device to have a microphone
# ios.requires_mic = 

# (list) iOS permissions
# ios.permissions = 

# (str) iOS app store
# ios.store = 

# (str) iOS app store key
# ios.store.key = 

# (str) iOS app store key alias
# ios.store.key.alias = 

# (str) iOS app store password
# ios.store.password = 

# (str) iOS app store key password
# ios.store.key.password = 

# (str) iOS app store team
# ios.store.team = 

# (list) iOS app frameworks
# ios.frameworks = 

# (bool) Enable iOS app signing
# ios.codesign.allowed = 

# (str) iOS app signing certificate
# ios.codesign.certificate = 

# (str) iOS app signing provisioning profile
# ios.codesign.provisioning_profile =

# (str) iOS app signing entitlements
# ios.codesign.entitlements = 

# (str) iOS app signing resource rules
# ios.codesign.resource_rules = 

# (str) iOS app signing keychain
# ios.codesign.keychain = 

# (str) macOS app icon
# macos.app_icon = 

# (str) macOS app category
# macos.category = 

# (list) macOS permissions
# macos.permissions = 

# (str) macOS app store
# macos.store = 

# (str) macOS app store key
# macos.store.key = 

# (str) macOS app store key alias
# macos.store.key.alias = 

# (str) macOS app store password
# macos.store.password = 

# (str) macOS app store key password
# macos.store.key.password = 

# (str) macOS app store team
# macos.store.team = 

# (list) macOS app frameworks
# macos.frameworks = 

# (bool) Enable macOS app signing
# macos.codesign.allowed = 

# (str) macOS app signing certificate
# macos.codesign.certificate = 

# (str) macOS app signing provisioning profile
# macos.codesign.provisioning_profile =

# (str) macOS app signing entitlements
# macos.codesign.entitlements = 

# (str) macOS app signing resource rules
# macos.codesign.resource_rules = 

# (str) macOS app signing keychain
# macos.codesign.keychain = 

# (str) Windows app icon
# windows.app_icon = 

# (str) Windows app version
# windows.version = 

# (str) Windows app GUID
# windows.guid = 

# (str) Windows app publisher
# windows.publisher = 

# (list) Windows app permissions
# windows.permissions = 

# (str) Windows app store
# windows.store = 

# (str) Windows app store key
# windows.store.key = 

# (str) Windows app store key alias
# windows.store.key.alias = 

# (str) Windows app store password
# windows.store.password = 

# (str) Windows app store key password
# windows.store.key.password = 

# (str) Windows app store team
# windows.store.team = 

# (list) Windows app frameworks
# windows.frameworks = 

# (bool) Enable Windows app signing
# windows.codesign.allowed = 

# (str) Windows app signing certificate
# windows.codesign.certificate = 

# (str) Windows app signing provisioning profile
# windows.codesign.provisioning_profile =

# (str) Windows app signing entitlements
# windows.codesign.entitlements = 

# (str) Windows app signing resource rules
# windows.codesign.resource_rules = 

# (str) Windows app signing keychain
# windows.codesign.keychain = 

# (str) Linux app icon
# linux.app_icon = 

# (str) Linux app category
# linux.category = 

# (list) Linux permissions
# linux.permissions = 

# (str) Linux app store
# linux.store = 

# (str) Linux app store key
# linux.store.key = 

# (str) Linux app store key alias
# linux.store.key.alias = 

# (str) Linux app store password
# linux.store.password = 

# (str) Linux app store key password
# linux.store.key.password = 

# (str) Linux app store team
# linux.store.team = 

# (list) Linux app frameworks
# linux.frameworks = 

# (bool) Enable Linux app signing
# linux.codesign.allowed = 

# (str) Linux app signing certificate
# linux.codesign.certificate = 

# (str) Linux app signing provisioning profile
# linux.codesign.provisioning_profile =

# (str) Linux app signing entitlements
# linux.codesign.entitlements = 

# (str) Linux app signing resource rules
# linux.codesign.resource_rules = 

# (str) Linux app signing keychain
# linux.codesign.keychain =