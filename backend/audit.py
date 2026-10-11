import os
import re
import json

def audit():
    output = {}

    def get_files(path, ext=None):
        files = []
        for root, _, fs in os.walk(path):
            if 'node_modules' in root or '__pycache__' in root or '.git' in root or 'venv' in root or 'dist' in root:
                continue
            for f in fs:
                if ext is None or f.endswith(ext):
                    files.append(os.path.join(root, f))
        return files

    be_files = get_files(r'E:\City_Care\backend', ('.py', '.md', '.txt'))
    fe_files = get_files(r'E:\City_Care\frontend', ('.ts', '.tsx', '.json', '.html'))
    docs = get_files(r'E:\City_Care\docs', ('.md'))

    output['frontend_pages'] = [f for f in fe_files if 'pages' in f]
    output['frontend_components'] = [f for f in fe_files if 'components' in f]
    output['backend_routers'] = [f for f in be_files if 'endpoints' in f]
    output['backend_models'] = [f for f in be_files if 'models' in f and 'ai_model' not in f]
    output['tests'] = [f for f in be_files if 'test_' in f]

    output['ai_models'] = get_files(r'E:\City_Care\backend\app\ai_model')

    # check test execution if possible, but actually we will just parse them.
    # checking joblibs
    output['joblibs'] = get_files(r'E:\City_Care\backend', ('.joblib', '.pt'))

    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    audit()
