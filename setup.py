from setuptools import setup, find_packages

setup(
  name='ASL-parameters-generator',
  version='1.0.0',
  packages=find_packages(),  # Automatically find packages in your project
  py_modules=['backend.json_validation', 'backend.validator'],  # Include your modules here
  install_requires=[
    'blinker==1.8.2',
    'click==8.1.7',
    'Flask==3.0.3',
    'Flask-Cors==4.0.1',
    'gunicorn==22.0.0',
    'itsdangerous==2.2.0',
    'Jinja2==3.1.4',
    'MarkupSafe==2.1.5',
    'packaging==24.0',
    'Werkzeug==3.0.3'
  ],
  include_package_data=True,  # Include additional files specified in MANIFEST.in
  description='A brief description of your project',  # Short description of your project
  author='Hanliang Xu',  # Your name
  author_email='hxu110@jh.edu',  # Your email
  url='https://github.com/Hanliang-Xu/Hanliang-Xu.github.io',  # URL to your project's repository
  classifiers=[
    'Programming Language :: Python :: 3',
    'Framework :: Flask',
    'Operating System :: OS Independent',
  ],
  python_requires='>=3.6',  # Specify the Python versions you support
)
