# BlurGuard Video Privacy Toolkit

**Open-source video privacy, censorship and motion tracking toolkit built with Python and OpenCV.**

BlurGuard Video Privacy Toolkit is a desktop video processing project designed to blur sensitive regions in video footage. It includes two applications:

- **BlurGuard Pro** — automatic face detection, CSRT tracking, manual sensitive-region selection, configurable blur strength and periodic face re-detection.
- **BlurGuard Lite** — lightweight manual region selection with MOSSE tracking and Gaussian blur.

Repository: https://github.com/ebubekirbastama/BlurGuard-Video-Privacy-Toolkit

## Features

### BlurGuard Pro

- Automatic face detection
- Automatic face blurring
- CSRT object tracking
- Manual sensitive-region selection
- Multiple region tracking
- Adjustable blur strength
- Adjustable face detection interval
- Periodic face re-detection to reduce tracker drift
- Progress indicator
- Modern CustomTkinter interface
- Original audio preservation with FFmpeg when available
- MP4 output

### BlurGuard Lite

- Manual sensitive-region selection
- Multiple region selection
- MOSSE object tracking
- Gaussian blur
- Adjustable blur intensity
- Region removal and clear-all controls
- Processing progress indicator
- FFmpeg audio preservation when available
- Simple Tkinter interface
- MP4 output

## Typical Use Cases

BlurGuard can assist with privacy-oriented video workflows such as:

- Journalism and newsroom footage
- Investigative reporting
- Face anonymization
- License plate or document obscuring
- Sensitive information censorship
- Security-camera footage preparation
- Research video preprocessing
- Social-media publishing

Automatic detection and tracking are not perfect. Review the full exported video before publication or distribution.

## Requirements

Python 3 is required.

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Equivalent direct installation:

```bash
pip install opencv-contrib-python Pillow numpy customtkinter
```

## FFmpeg

FFmpeg is strongly recommended because the applications process video frames separately and then attempt to restore the original audio stream.

Check whether FFmpeg is available:

```bash
ffmpeg -version
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

### Windows

Install FFmpeg and add its `bin` directory to the Windows `PATH` environment variable.

If FFmpeg is not available, the processed video may be saved without the original audio.

## Installation

Clone the repository:

```bash
git clone https://github.com/ebubekirbastama/BlurGuard-Video-Privacy-Toolkit.git
cd BlurGuard-Video-Privacy-Toolkit
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run BlurGuard Pro

```bash
python blurguard_pro.py
```

or:

```bash
python3 blurguard_pro.py
```

BlurGuard Pro combines automatic face censorship with manually selected sensitive areas. It uses CSRT tracking for moving regions and periodically performs face detection again to help correct tracker drift and identify faces appearing later in the video.

## Run BlurGuard Lite

```bash
python blurguard_lite.py
```

or:

```bash
python3 blurguard_lite.py
```

BlurGuard Lite displays the first frame of the selected video and lets the user draw one or more sensitive regions. Those regions are followed through the video with MOSSE trackers and blurred using Gaussian blur.

## How BlurGuard Pro Works

1. Select a video.
2. Keep automatic face censorship enabled if desired.
3. Optionally select one or more manual sensitive regions.
4. Adjust blur strength.
5. Adjust the face detection refresh interval if needed.
6. Start processing and choose an output MP4 file.
7. Review the final video before publishing it.

## How BlurGuard Lite Works

1. Open a video.
2. Draw rectangles around sensitive areas in the first frame.
3. Remove incorrect regions if necessary.
4. Adjust blur strength.
5. Click the processing button and choose an output MP4 file.
6. Review the final result.

## Motion Tracking

### CSRT — BlurGuard Pro

BlurGuard Pro uses OpenCV's CSRT tracker. CSRT generally provides more robust tracking than lightweight trackers when the tracked object's position, scale or appearance changes.

### MOSSE — BlurGuard Lite

BlurGuard Lite uses the MOSSE tracker. MOSSE is lightweight and fast, making it suitable for simpler manual tracking workflows.

## Face Detection

BlurGuard Pro uses OpenCV's Haar Cascade frontal-face detector. Detected faces can be initialized as trackers and re-detected at intervals while processing continues.

Face detection may fail because of factors such as:

- Extreme head angles
- Poor lighting
- Motion blur
- Occlusion
- Very small faces
- Sudden scene changes

Always inspect the exported video manually.

## Audio Preservation

The basic processing flow is:

```text
Original Video
     |
     +--> Video Frames --> BlurGuard --> Processed Video
     |
     +--> Original Audio --------------------+
                                               |
                                               v
                                            FFmpeg
                                               |
                                               v
                                         Final MP4 Video
```

If FFmpeg is unavailable, the applications may fall back to a silent processed video.

## Privacy

The applications are designed to process videos locally on the user's computer. They do not require an online upload workflow as part of the program itself.

Users remain responsible for handling source footage and exported files according to their own privacy, security and legal requirements.

## Limitations

Tracking and computer-vision detection are probabilistic and can fail. Accuracy can decrease because of:

- Fast movement
- Motion blur
- Occlusion
- Camera shake
- Poor lighting
- Objects leaving and re-entering the frame
- Sudden scene changes
- Tracker drift

For journalism, privacy-sensitive footage or other critical workflows, manually review the entire exported video before publication.

## Project Structure

```text
BlurGuard-Video-Privacy-Toolkit/
|
+-- blurguard_pro.py
+-- blurguard_lite.py
+-- requirements.txt
+-- README.md
+-- LICENSE
+-- .gitignore
+-- screenshots/
+-- examples/
```

## Technology Stack

- Python
- OpenCV / OpenCV Contrib
- Tkinter
- CustomTkinter
- Pillow
- FFmpeg
- CSRT tracking
- MOSSE tracking
- Gaussian blur
- Haar Cascade face detection

## Contributing

Contributions, bug reports and feature requests are welcome.

Typical workflow:

```bash
git checkout -b feature/my-improvement
git add .
git commit -m "Add improvement"
git push origin feature/my-improvement
```

Then open a pull request on GitHub.

## Possible Future Improvements

- Deep-learning-based face detection
- Automatic license plate detection
- YOLO-based object detection
- GPU acceleration
- Real-time processing preview
- Improved tracker recovery
- Batch video processing
- Command-line interface
- Pixelation mode
- Black-box censorship mode
- Cross-platform executable builds

## Disclaimer

BlurGuard Video Privacy Toolkit is provided as a general-purpose video privacy and censorship tool. Users are responsible for reviewing processed videos and confirming that sensitive content has been adequately obscured before publication or distribution.

The software is provided without warranty.

## License

Copyright 2026 Ebubekir Bastama

Licensed under the **Apache License, Version 2.0**.

See the `LICENSE` file for the complete license text.

## Author

**Ebubekir Bastama**

GitHub: https://github.com/ebubekirbastama

If the project is useful, consider starring the repository.
