import subprocess
import pexpect
import os
import sys
import pwd
from charms.reactive import when, when_not, set_state
from charmhelpers.core import hookenv, host, templating
from charmhelpers.core.hookenv import status_set
from jujubigdata import utils
import charms.apt

@when_not('superset.installed')
@when('apt.installed.build-essential',
      'apt.installed.libssl-dev',
      'apt.installed.libffi-dev',
      'apt.installed.python3-dev',
      'apt.installed.python3-pip',
      'apt.installed.libsasl2-dev',
      'apt.installed.libldap2-dev')
def install_superset():
    status_set('maintenance', 'Installing superset')
    #init_virtualenv()
    hookenv.log('Installing Superset')
    subprocess.check_call(['pip3','install', '--upgrade', 'setuptools', 'pip'])
    subprocess.check_call(['pip3','install', 'superset'])
    set_state('superset.installed')

    hookenv.log('Switching to user ubuntu')
    subprocess.check_call(['su', '-', 'ubuntu'])
    hookenv.log('whoami: %s' % subprocess.check_output(['whoami']).strip())
    hookenv.log('cat /etc/passwd | grep ubuntu: %s' % subprocess.check_output('cat /etc/passwd | grep ubuntu', shell=True).strip())
    hookenv.log('cwd: %s' % os.getcwd())

@when('superset.installed')
@when_not('superset.configured')
def superset_setup():
    status_set('maintenance', 'Configuring superset')
    # Setting LC_ALL and LANG vbles
    os.environ['LC_ALL'] = 'C.UTF-8'
    os.environ['LANG'] = 'C.UTF-8'

    # Initialize the database
    hookenv.log('Initialize the database')
    subprocess.check_call(['su', '-', 'ubuntu', '-c', 'superset db upgrade'])
    # Load some data to play with
    hookenv.log('Load some data to play with')
    subprocess.check_call(['su', '-', 'ubuntu', '-c', 'superset load_examples'])

    set_state('superset.configured')

@when('superset.installed',
      'superset.configured')
@when_not('superset.ready')
def superset_startup():

    superset_dir = '/home/ubuntu/superset'
    db_uri = 'sqlite:////home/ubuntu/.superset/superset.db'
    context = {
        'db_uri': db_uri
    }
    host.mkdir(superset_dir)
    templating.render(
        source='superset_config.py.jinja2',
        target=superset_dir + '/superset_config.py',
        context=context
    )

    with utils.environment_edit_in_place('/etc/environment') as env:
        # Appending superset_config.py to the PYTHONPATH
        env['PYTHONPATH'] = "$PYTHONPATH:%s" % (superset_dir + '/superset_config.py')

    # Create an admin user (you will be prompted to set username, first and last name before setting a password)
    # Username [admin]:
    # User first name [admin]:
    # User last name [user]:
    # Email [admin@fab.org]:
    # Password:
    # Repeat for confirmation:
    hookenv.log('Creating admin user for Superset')
    child = pexpect.spawn("su - ubuntu -c \"fabmanager create-admin --app superset\"")
    child.expect('\\r\\nUsername \[admin\]: ')
    child.sendline()
    child.expect('\\r\\nUser first name \[admin\]: ')
    child.sendline()
    child.expect('\\r\\nUser last name \[user\]: ')
    child.sendline()
    child.expect('\\r\\nEmail \[admin@fab.org\]: ')
    child.sendline()
    child.expect('\\r\\nPassword: ')
    child.sendline('admin')
    child.expect('\\r\\nRepeat for confirmation: ')
    child.sendline('admin')

    # Create default roles and permissions
    hookenv.log('Create default roles and permissions')
    #subprocess.check_call(['superset', 'init'])
    subprocess.check_call(['su', '-', 'ubuntu', '-c', 'superset init'])
    # Start the web server on port 8088, use -p to bind to another port
    hookenv.log('Start the web server on port 8088')
    #subprocess.Popen(['superset', 'runserver'])
    subprocess.Popen(['su', '-', 'ubuntu', '-c', 'superset runserver'])

    set_state('superset.ready')
    status_set('active', 'Superset up and running')
