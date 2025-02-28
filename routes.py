import json
import subprocess
import os
from flask import Response, request, render_template_string, jsonify, send_from_directory
from ripper import Rip_Collection, dvd_dump_dir, mkv_dump_dir
from templates import form_template


def init_routes(app):
    Rip_Collection.scan(dvd_dump_dir)

    @app.route('/')
    def index():
        return render_template_string(form_template)

    @app.route('/get_table_data')
    def get_table_data():
        return jsonify(Rip_Collection.to_dict())

    @app.route('/update/<int:id>', methods=['POST'])
    def update(id):
        new_title = request.form['title']
        rip=Rip_Collection.get_by_id(id)
        if rip is None: return jsonify(status="Not found")
        rip.set_title(new_title)
        rip.status = "Updated"
        return jsonify(rip.to_dict())

    @app.route('/delete/<int:id>', methods=['POST'])
    def delete(id):
        Rip_Collection.remove([rip for rip in Rip_Collection.items if rip.id == id])
        return jsonify(success=True)

    @app.route('/delete_mkv_file/<int:id>', methods=['POST'])
    def delete_mkv_file(id):
        filename = request.form['filename']
        rip=Rip_Collection.get_by_id(id)
        if rip is None: return jsonify(success=False)
        rip.delete_mkv_file(filename)
        rip.status = "MKV File Deleted"
        return jsonify(rip.to_dict())

    @app.route('/rename/<int:id>', methods=['POST'])
    def rename(id):
        rip=Rip_Collection.get_by_id(id)
        if rip is None: return jsonify(status="File not found")

        filenamesMapped=json.loads(request.form.get("Filenames"))
        for filenameset in filenamesMapped:
            fileitem = rip.get_mkv_file(filenameset["filename"])
            if fileitem is None: continue
            fileitem.rename_to=filenameset["rename_to"]
        rip.do_rename()

        rip.status = "MKV Files Renamed"
        return jsonify(rip.to_dict()) 


    @app.route('/rename_based_on_title/<int:id>', methods=['POST'])
    def rename_based_on_title(id):
        for rip in Rip_Collection.items:
            if rip.id == id:
                rip.mass_rename_mkv(rip.title)
                rip.do_rename()
                rip.status = "MKV Files Renamed Based on Title"
                mkv_files = [{'filename': file.filename, 'size': file.size} for file in rip.mkv_dump_files]
                break
        return jsonify(rip.to_dict())
        return jsonify(status=rip.status, mkv_files=mkv_files)


    @app.route('/video/<path>/<video_file>')
    def video_feed(path:str,video_file:str):
        """Stream video from the beginning without seeking."""
        response = Response(stream_video_ffmpeg(path+'/'+video_file), mimetype="video/mp4")
        return response

    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('static', filename)

def stream_video_ffmpeg(video_file:str):
    """Runs FFmpeg to transcode and stream video from a specific timestamp."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", os.path.join(mkv_dump_dir, video_file),          # Input file
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
