from flask import Flask, request, render_template_string, jsonify
from ripper import *

app = Flask(__name__)

Rip_Collection.scan(dvd_dump_dir)

for rip_item in Rip_Collection.items:
    print(rip_item)

form_template_bare = """
    <form action="/submit" method="post">
      <label for="arg1">Argument 1:</label>
      <input type="text" id="arg1" name="arg1" value="{{arg1}}"><br><br>
      <label for="arg2">Argument 2:</label>
      <input type="text" id="arg2" name="arg2" value="{{arg2}}"><br><br>
      <input type="submit" value="Submit">
    </form>
"""

# HTML template for the form and table with CSS and JavaScript
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
        min-width: 100px;
        max-width: 100px;
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
        data.forEach(function(rip) {
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
              document.querySelector('#rip-' + id + ' input[name="mkv_filename_' + (i + 1) + '"]').value = mkvFiles[i];
            }
          }
        };
        xhr.send();
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
  </body>
</html>
"""

# Function to be called with form arguments
def example_function(arg1, arg2):
    return f"Function called with arguments: {arg1}, {arg2}" 

@app.route('/')
def index():
    return render_template_string(form_template)

@app.route('/get_table_data')
def get_table_data():
    data = []
    for rip in Rip_Collection.items:
        rip_data = {
            'id': rip.id,
            'title': rip.title,
            'device': rip.device,
            'dvd_dump_path': rip.dvd_dump_path,
            'mkv_dump_path': rip.mkv_dump_path,
            'status': rip.status,
            'mkv_dump_files': [{'filename': file.filename, 'size': file.size} for file in rip.mkv_dump_files]
        }
        data.append(rip_data)
    return jsonify(data)

@app.route('/submit', methods=['POST'])
def submit():
    arg1 = request.form['arg1']
    arg2 = request.form['arg2']
    result = example_function(arg1, arg2)
    return render_template_string(f"<h1>{result}</h1>{form_template_bare}", arg1=arg1, arg2=arg2)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    # Handle the update logic here
    new_title = request.form['title']
    for rip in Rip_Collection.items:
        if rip.id == id:
            rip.title = new_title
            rip.status = "Updated"
            break
    return jsonify(status=rip.status)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    # Handle the delete logic here
    Rip_Collection.items = [rip for rip in Rip_Collection.items if rip.id != id]
    return jsonify(success=True)

@app.route('/delete_mkv_file/<int:id>', methods=['POST'])
def delete_mkv_file(id):
    # Handle the delete MKV file logic here
    filename = request.form['filename']
    for rip in Rip_Collection.items:
        if rip.id == id:
            rip.delete_mkv_file(filename)
            rip.status = "MKV File Deleted"
            break
    return jsonify(success=True)

@app.route('/rename/<int:id>', methods=['POST'])
def rename(id):
    # Handle the rename logic here
    for rip in Rip_Collection.items:
        if rip.id == id:
            for i, file in enumerate(rip.mkv_dump_files, start=1):
                new_filename = request.form.get(f'mkv_filename_{i}')
                if new_filename:
                    file.rename_to = new_filename
            rip.do_rename()
            rip.status = "MKV Files Renamed"
            break
    return jsonify(status=rip.status)

@app.route('/rename_based_on_title/<int:id>', methods=['POST'])
def rename_based_on_title(id):
    # Handle the rename based on title logic here
    for rip in Rip_Collection.items:
        if rip.id == id:
            rip.mass_rename_mkv(rip.title)
            rip.do_rename()
            rip.status = "MKV Files Renamed Based on Title"
            mkv_files = [file.filename for file in rip.mkv_dump_files]
            break
    return jsonify(status=rip.status, mkv_files=mkv_files)

if __name__ == '__main__':
    app.run(debug=True)