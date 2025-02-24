form_template = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Rips</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 20px;
        background-color: #f0f0f0;
      }
      h1 {
        color: #333;
        text-align: center;
      }
      .container {
        min-width: 1800px;
        margin: 0 auto;
        background-color: #fff;
        padding: 20px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
      }
      th, td {
        padding: 12px;
        border: 1px solid #ddd;
        text-align: left;
        vertical-align: top;
      }
      th {
        background-color: #f4f4f4;
      }
      tr:nth-child(even) {
        background-color: #f9f9f9;
      }
      tr:hover {
        background-color: #f1f1f1;
      }
      .actions {
        display: flex;
        gap: 10px;
        width: 50px;
      }
      .actions button {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 16px;
      }
      .actions button:hover {
        color: #007BFF;
      }
      .refresh-button {
        display: block;
        margin: 20px auto;
        background: #007BFF;
        color: #fff;
        border: none;
        padding: 10px 20px;
        cursor: pointer;
        font-size: 16px;
        border-radius: 5px;
      }
      .refresh-button:hover {
        background: #0056b3;
      }
      .mkv-file {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 5px;
      }
      .mkv-size {
        flex: 1;
        text-witdth=100px
        text-align: right;
      }
      .mkv-file input {
        flex: 1;
        min-width: 300px;
        max-width: 300px;
      }
      .mkv-file button {
        flex-shrink: 0;
      }
      .mkv-preview {
        flex: 1;
        min-width: 300px;
        max-width: 300px;
      }
      .unsupported-format {
        color: red;
        font-weight: bold;
      }
      .popup {
        display: none;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: white;
        padding: 20px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        z-index: 1000;
      }
      .popup video {
        width: 100%;
        height: auto;
      }
      .popup-close {
        position: absolute;
        top: 10px;
        right: 10px;
        cursor: pointer;
      }
      .overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 999;
      }
    </style>
    <script>
      function loadTable() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/get_table_data', true);
        xhr.onreadystatechange = function () {
          if (xhr.readyState == 4 && xhr.status == 200) {
            var data = JSON.parse(xhr.responseText);
            var tableContainer = document.getElementById('table-container');
            tableContainer.innerHTML = createTable(data);
          }
        };
        xhr.send();
      }

      function createTable(data) {
        var table = '<table>';
        table += '<tr><th>ID</th><th>Title</th><th>Device</th><th>DVD Dump Path</th><th>MKV Dump Path</th><th>Status</th><th>MKV Files</th><th>Actions</th></tr>';
        data.items.forEach(function(rip) {
          table += '<tr id="rip-' + rip.id + '">';
          table += '<td>' + rip.id + '</td>';
          table += '<td><input type="text" id="title-' + rip.id + '" name="title" value="' + rip.title + '"></td>';
          table += '<td>' + rip.device + '</td>';
          table += '<td>' + rip.dvd_dump_path + '</td>';
          table += '<td>' + rip.mkv_dump_path + '</td>';
          table += '<td id="status-' + rip.id + '">' + rip.status + '</td>';
          table += '<td>';
          rip.mkv_dump_files.forEach(function(file, index) {
            table += '<div class="mkv-file" data-filename="' + file.filename + '">';
            table += '<input type="text" name="mkv_filename_' + (index + 1) + '" value="' + file.filename + '">';
            table += '<div class="mkv-size">' + (file.size / (1024 * 1024)).toFixed(2) + ' MB</div>';
            table += '<button title="Delete MKV File" onclick="deleteMKVFile(' + rip.id + ', \\'' + file.filename + '\\')"><i class="fas fa-trash-alt"></i></button>';
            if (file.filename.endsWith('.mkv')) {
              table += '<button title="Preview MKV File" onclick="openVideoPopup(\\'' + rip.title + '\\', \\'' + file.filename + '\\')"><i class="fas fa-play"></i></button>';
            } else {
              table += '<div class="unsupported-format">Unsupported format</div>';
            }
            table += '</div>';
          });
          table += '</td>';
          table += '<td class="actions">';
          table += '<button title="Update Title" onclick="updateTitle(' + rip.id + ')"><i class="fas fa-save"></i></button>';
          table += '<button title="Rename MKV Files" onclick="renameMKVFiles(' + rip.id + ')"><i class="fas fa-edit"></i></button>';
          table += '<button title="Rename MKV Files Based on Title" onclick="renameMKVFilesBasedOnTitle(' + rip.id + ')"><i class="fas fa-sync-alt"></i></button>';
          table += '<button title="Delete Rip" onclick="deleteRip(' + rip.id + ')"><i class="fas fa-trash-alt"></i></button>';
          table += '</td>';
          table += '</tr>';
        });
        table += '</table>';
        return table;
      }

      function updateTitle(id) {
        var title = document.getElementById('title-' + id).value;
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/update/' + id, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
          if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            document.getElementById('status-' + id).innerText = response.status;
          }
        };
        xhr.send('title=' + encodeURIComponent(title));
      }

      function deleteRip(id) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/delete/' + id, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
          if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
              var row = document.getElementById('rip-' + id);
              row.parentNode.removeChild(row);
            }
          }
        };
        xhr.send();
      }

      function deleteMKVFile(ripId, filename) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/delete_mkv_file/' + ripId, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
          if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
              var fileRow = document.querySelector('#rip-' + ripId + ' div[data-filename="' + filename + '"]');
              fileRow.parentNode.removeChild(fileRow);
            }
          }
        };
        xhr.send('filename=' + encodeURIComponent(filename));
      }

      function renameMKVFiles(id) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/rename/' + id, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
          if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            document.getElementById('status-' + id).innerText = response.status;
          }
        };
        var formData = new FormData();
        var inputs = document.querySelectorAll('#rip-' + id + ' input[name^="mkv_filename_"]');
        inputs.forEach(function(input) {
          formData.append(input.name, input.value);
        });
        xhr.send(new URLSearchParams(formData).toString());
      }

      function renameMKVFilesBasedOnTitle(id) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/rename_based_on_title/' + id, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onreadystatechange = function () {
          if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            document.getElementById('status-' + id).innerText = response.status;
            var mkvFiles = response.mkv_files;
            for (var i = 0; i < mkvFiles.length; i++) {
              document.querySelector('#rip-' + id + ' input[name="mkv_filename_' + (i + 1) + '"]').value = mkvFiles[i].filename;
            }
          }
        };
        xhr.send();
      }

      function openVideoPopup(path, filename) {
        var popup = document.getElementById('video-popup');
        var overlay = document.getElementById('overlay');
        var video = document.getElementById('popup-video');
        video.src = '/video/' + path + '/' + filename;
        popup.style.display = 'block';
        overlay.style.display = 'block';
      }

      function closeVideoPopup() {
        var popup = document.getElementById('video-popup');
        var overlay = document.getElementById('overlay');
        var video = document.getElementById('popup-video');
        video.pause();
        video.src = '';
        popup.style.display = 'none';
        overlay.style.display = 'none';
      }

      document.addEventListener('DOMContentLoaded', function() {
        loadTable();
      });
    </script>
  </head>
  <body>
    <div class="container">
      <h1>Rips</h1>
      <button class="refresh-button" onclick="loadTable()">Refresh Table</button>
      <div id="table-container"></div>
      {{ form_template_bare | safe }}
    </div>
    <div id="overlay" class="overlay" onclick="closeVideoPopup()"></div>
    <div id="video-popup" class="popup">
      <span class="popup-close" onclick="closeVideoPopup()">&times;</span>
      <video id="popup-video" controls>
        <source src="" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    </div>
  </body>
</html>
"""