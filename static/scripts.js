/* filepath: /home/kenneth/python/dvdripper/static/scripts.js */
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
  table += '<tr><th class="id">ID</th><th class="title">Title</th><th class="device">Device</th><th class="path">DVD Dump Path</th><th class="path">MKV Dump Path</th><th class="status">Status</th><th class="mkv-files">MKV Files</th><th class="actions">Actions</th></tr>';
  data.items.forEach(function(rip) {
    table += '<tr id="rip-' + rip.id + '">';
    table += '<td class="id">' + rip.id + '</td>';
    table += '<td class="title"><input class="title" type="text" id="title-' + rip.id + '" name="title" value="' + rip.title + '"></td>';
    table += '<td class="device">' + rip.device + '</td>';
    table += '<td class="path">' + rip.dvd_dump_path + '</td>';
    table += '<td class="path">' + rip.mkv_dump_path + '</td>';
    table += '<td class="status" id="status-' + rip.id + '">' + rip.status + '</td>';
    table += '<td class="mkv">';
    rip.mkv_dump_files.forEach(function(file, index) {
      table += '<div class="mkv-file" data-filename="' + file.filename + '">';
      table += '<input class="mkv-file" type="text" name="mkv_filename_' + (index + 1) + '" value="' + file.filename + '">';
      table += '<div class="mkv-size">' + (file.size / (1024 * 1024)).toFixed(2) + ' MB</div>';
      table += '<button title="Delete MKV File" onclick="deleteMKVFile(' + rip.id + ', \'' + file.filename + '\')"><i class="fas fa-trash-alt"></i></button>';
      if (file.filename.endsWith('.mkv')) {
        table += '<button title="Preview MKV File" onclick="openVideoPopup(\'' + rip.title + '\', \'' + file.filename + '\')"><i class="fas fa-play"></i></button>';
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
    // Clear any existing sources
    while (video.firstChild) {
      video.removeChild(video.firstChild);
    }
  
    // Create and add the new source element
    var source = document.createElement('source');
    source.src = '/video/' + path + '/' + filename;
    source.type = 'video/mp4';
    video.appendChild(source);
  
    popup.style.display = 'block';
    overlay.style.display = 'block';

    video.load();
    video.play();
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