Album App for web2py
====================

ReportBro album application for web2py web framework (2.18.5+). This is a fully
working demo app to showcase ReportBro and how you can integrate it in your web2py application.

The application is a simple web app and allows to manage a list of music albums.
ReportBro Designer is included so you can modify a template which is used
when you print a pdf of all your albums.

The Demo App is also avaiable for the `Django <https://www.djangoproject.com/>`_
and `Flask <https://palletsprojects.com/p/flask/>`_ web frameworks. See
`Album App for Django <https://github.com/jobsta/albumapp-django.git>`_ and
`Album App for Flask <https://github.com/jobsta/albumapp-flask.git>`_ respectively.

All Instructions in this file are for a Linux/Mac shell but the commands should
be easy to adapt for Windows.

Installation
------------

Download `web2py source code <http://web2py.com/init/default/download>`_ for
Python 3.x and unpack the zip file (if you don't have web2py 2.18.5+ installed already).

Change into web2py applications directory:

.. code:: shell

    $ cd web2py/applications

Clone the git repository:

.. code:: shell

    $ git clone https://github.com/jobsta/albumapp-web2py.git albums

Create a virtual environment in web2py root directory called env:

.. code:: shell

    $ cd ..
    $ python3 -m venv env

Activate the virtual environment:

.. code:: shell

    $ . env/bin/activate

Install reportbro-lib:

.. code:: shell

    $ pip install reportbro-lib

Configuration
-------------

No additional configuration is needed because the database and its tables
are automatically created by web2py.

Run App
-------

Activate the virtual environment (if not already active):

.. code:: shell

    $ . env/bin/activate

Start the web2py webserver (with default password for admin console):

.. code:: shell

    $ python web2py.py --password=123

Now your application is running and can be accessed here:
http://127.0.0.1:8000/albums

IDE Configuration (PyCharm)
---------------------------

1. Open web2py directory

2. Add virtual env to project:

- Select File -> Settings
- Project: web2py -> Project interpreter
- click Settings-Icon and select "Add Local" option, select the recently created virtual env

3. Edit Configurations...

- Python interpreter: select virtual env (if not already set)
- Script parameters: --password=123

Python Coding Style
-------------------

The `PEP 8 (Python Enhancement Proposal) <https://www.python.org/dev/peps/pep-0008/>`_
standard is used which is the de-facto code style guide for Python. An easy-to-read version
of PEP 8 can be found at https://pep8.org/
