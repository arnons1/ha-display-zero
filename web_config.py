from flask import Flask, render_template_string, request
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = '''
<h1>E-Ink Dashboard Config</h1>
<form action="/refresh" method="post">
    <button type="submit">Refresh Display Now</button>
</form>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/refresh', methods=['POST'])
def refresh():
    # Runs your monitor script manually
    subprocess.run(["python3", "monitor.py"])
    return "Display Updating..."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
