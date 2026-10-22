REELS SPLITTER — VISUAL EDITOR (Windows)

WHAT THIS BUILD DOES
- Launches two separate layout windows when the app starts (if the required input files are present): Thumbnail Editor and Video Overlay Editor.
- Both editors have independent saved layouts, Save/Cancel buttons, and a confirmation prompt before saving.
- Drag a dashed box to move it; drag the bottom-right square to resize it. Ghost labels and outlines are editor-only and never appear in exported media.
- Title style: bold metallic white/blue text with dark outline and shadow. Part label: italic yellow text inside a dark rounded badge with a white border. Text automatically shrinks to fit its box.
- Portrait export is 1080x1920. Landscape source video keeps its original aspect ratio, is fitted inside the selected video box, and is never intentionally cropped or stretched.
- The portrait background fills the canvas and is blurred/darkened behind the video.
- Uses NVIDIA H.264 NVENC when FFmpeg reports it available; if NVENC fails, retries with CPU x264. NVENC uses the fast p2 preset and CQ 20. CPU fallback uses veryfast/CRF 20.
- Prints live per-part progress in the console.
- Supporting code, settings, and temporary files live under bin/.

REQUIREMENTS
1. Windows 10/11.
2. Python 3.10+ from https://www.python.org/downloads/ (tick "Add python.exe to PATH").
3. FFmpeg + FFprobe installed and available on PATH. Your FFmpeg should support h264_nvenc for GPU encoding. Test with `ffmpeg -encoders | findstr nvenc` in Command Prompt.
4. Pillow. run.bat attempts to install it automatically if missing.

HOW TO USE
1. Extract the ZIP to a normal writable folder (not inside Program Files or a protected folder).
2. Put exactly one landscape video in input/video/.
3. Put exactly one background image in input/background/.
4. Double-click run.bat. The launcher opens and both editor windows appear.
5. Drag boxes to move them. Drag the small bottom-right handle to resize. The video box defines the maximum area; the landscape source is fitted inside it without cropping.
6. Click Save in each editor and confirm. Cancel discards unsaved layout changes. Layouts are saved separately in bin/layout_settings.json.
7. Enter the desired title and segment duration in the main launcher, then click Render Reels.
8. Finished MP4 files are written to output/ as Part1.mp4, Part2.mp4, etc.

SPLITTING BEHAVIOUR
- Segment duration is the target source-footage duration per part.
- Adjacent source segments overlap by approximately 1 second (start interval = duration minus 1 second).
- Each output starts with a 1-second title card, followed by its source segment.
- If the source has audio, the title card is silent and source audio begins after the title card.

IMPORTANT
- This is an initial Windows project build. Python syntax and the FFmpeg filter graph were checked in a test environment, but it has not been tested on your exact PC. Test with a short video first.
- Editor boxes are movable/resizable and text auto-fits. This build does not yet expose every font/color/glow parameter in a dedicated style-properties panel; the fancy styling is included as the default.
- Keep the video and background folders to one supported file each. Supported video formats include MP4, MOV, MKV, AVI, WebM, M4V, MPEG; supported images include PNG, JPG/JPEG, WebP, BMP.
