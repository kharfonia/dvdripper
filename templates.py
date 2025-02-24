form_template = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Rips</title>
    <link rel="stylesheet" href="/static/styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
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
        <!-- Source will be added dynamically -->
        Your browser does not support the video tag.
      </video>
    </div>
    <script src="/static/scripts.js"></script>
  </body>
</html>
"""