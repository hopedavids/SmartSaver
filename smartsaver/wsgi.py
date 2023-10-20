import sys
import os

# Add the root directory of your project to the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from smartsaver_app import create_app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
