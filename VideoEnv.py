import os
import subprocess
from flask import Flask, Response, request

app = Flask(__name__)

VIDEO_PATH = "mkv_dump/FRIENDS_SERIES1_D1B/B1_t00.mkv"  # Change to your video file
VIDEO_PATH = "mkv_dump"  # Change to your video file


def stream_video_ffmpeg(video_file:str):
    """Runs FFmpeg to transcode and stream video from a specific timestamp."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", os.path.join(VIDEO_PATH, video_file),          # Input file
        "-c:v", "libx264",                                   # Encode video as H.264
        "-preset", "ultrafast",                              # Fast encoding
        "-b:v", "800k",                                      # Lower bitrate for fast streaming
        "-c:a", "aac",                                       # Encode audio as AAC
        "-b:a", "128k",                                      # Audio bitrate
        "-movflags", "+faststart+frag_keyframe+empty_moov",  # Streamable MP4
        "-f", "mp4",                                         # MP4 format
        "pipe:1"                                             # Output to stdout
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1024 * 1024)

    try:
        while True:
            chunk = process.stdout.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            yield chunk
    finally:
        process.stdout.close()
        process.wait()

@app.route('/video/<path>/<video_file>')
def video_feed(path:str,video_file:str):
    """Stream video from the beginning without seeking."""
    response = Response(stream_video_ffmpeg(path+'/'+video_file), mimetype="video/mp4")
    return response

@app.route('/')
def frontPage():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Seekable Video Stream</title>
</head>
<body>
    <video width="640" height="360" controls>
        <source src="http://localhost:5000/video/FRIENDS_SERIES1_D1B/B1_t00.mkv" type="video/mp4">
        Your browser does not support the video tag.
    </video>
</body>
</html>

"""


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
