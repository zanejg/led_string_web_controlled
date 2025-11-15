from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production


@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """API endpoint to get current status"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask app is running'
    })


@app.route('/api/data', methods=['POST'])
def post_data():
    """API endpoint to receive data"""
    data = request.get_json()
    # Process your data here
    return jsonify({
        'status': 'success',
        'received': data
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
