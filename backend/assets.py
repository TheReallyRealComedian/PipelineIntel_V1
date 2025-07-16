# backend/assets.py
from flask_assets import Bundle

js_main_bundle = Bundle(
    'js/main.js',
    filters='jsmin',
    output='gen/app.%(version)s.js'
)

css_bundle = Bundle(
    'css/style.css',
    filters='cssmin',
    output='gen/style.%(version)s.css'
)