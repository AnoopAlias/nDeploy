#!/usr/bin/python
import cgi
import cgitb
import subprocess
import os
import yaml
import platform
import psutil
import signal
import jinja2
import codecs

__author__ = "Anoop P Alias"
__copyright__ = "Copyright Anoop P Alias"
__license__ = "GPL"
__email__ = "anoopalias01@gmail.com"


installation_path = "/opt/nDeploy"  # Absolute Installation Path
backup_config_file = "/opt/nDeploy/conf/backup_config.yaml"
borgmatic_config_file = "/etc/borgmatic/config.yaml"

cgitb.enable()


# Define a function to silently remove files
def silentremove(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def safenginxreload():
    nginx_status = False
    for myprocess in psutil.process_iter():
        # Workaround for Python 2.6
        if platform.python_version().startswith('2.6'):
            mycmdline = myprocess.cmdline
        else:
            mycmdline = myprocess.cmdline()
        if '/usr/sbin/nginx' in mycmdline and 'reload' in mycmdline:
            nginx_status = True
            break
    if not nginx_status:
        with open(os.devnull, 'w') as FNULL:
            subprocess.Popen(['/usr/sbin/nginx', '-s', 'reload'], stdout=FNULL, stderr=subprocess.STDOUT)


def sighupnginx():
    for myprocess in psutil.process_iter():
        # Workaround for Python 2.6
        if platform.python_version().startswith('2.6'):
            mycmdline = myprocess.cmdline
        else:
            mycmdline = myprocess.cmdline()
        if 'nginx: master process /usr/sbin/nginx -c /etc/nginx/nginx.conf' in mycmdline:
            nginxpid = myprocess.pid
            os.kill(nginxpid, signal.SIGHUP)


def branding_print_logo_name():
    "Branding support"
    if os.path.isfile(installation_path+"/conf/branding.yaml"):
        with open(installation_path+"/conf/branding.yaml", 'r') as brand_data_file:
            yaml_parsed_brand = yaml.safe_load(brand_data_file)
        brand_logo = yaml_parsed_brand.get("brand_logo", "xtendweb.png")
    else:
        brand_logo = "xtendweb.png"
    return brand_logo


def branding_print_banner():
    "Branding support"
    if os.path.isfile(installation_path+"/conf/branding.yaml"):
        with open(installation_path+"/conf/branding.yaml", 'r') as brand_data_file:
            yaml_parsed_brand = yaml.safe_load(brand_data_file)
        brand_name = yaml_parsed_brand.get("brand", "AUTOM8N")
    else:
        brand_name = "AUTOM8N"
    return brand_name


def branding_print_footer():
    "Branding support"
    if os.path.isfile(installation_path+"/conf/branding.yaml"):
        with open(installation_path+"/conf/branding.yaml", 'r') as brand_data_file:
            yaml_parsed_brand = yaml.safe_load(brand_data_file)
        brand_footer = yaml_parsed_brand.get("brand_footer", '<a target="_blank" href="https://autom8n.com">A U T O M 8 N</a>')
    else:
        brand_footer = '<a target="_blank" href="https://autom8n.com">A U T O M 8 N</a>'
    return brand_footer


def print_green(theoption, hint):
    print(('<div class="col-sm-6"><div class="label label-info" data-toggle="tooltip" title="'+hint+'">'+theoption+'</div></div>'))


def print_red(theoption, hint):
    print(('<div class="col-sm-6"><div class="label label-default" data-toggle="tooltip" title="'+hint+'">'+theoption+'</div></div>'))


form = cgi.FieldStorage()

print('Content-Type: text/html')
print('')
print('<html>')
print('<head>')

print('<title>')
print(branding_print_banner())
print('</title>')

print(('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">'))
print(('<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js" crossorigin="anonymous"></script>'))
print(('<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>'))
print(('<script src="js.js"></script>'))
print(('<link rel="stylesheet" href="styles.css">'))
print('</head>')
print('<body>')
print('<div id="main-container" class="container text-center">')  # marker1
print('<div class="row">')  # marker2
print('<div class="col-md-6 col-md-offset-3">')  # marker3

print('<div class="logo">')
print('<a href="xtendweb.cgi"><img border="0" src="')
print(branding_print_logo_name())
print('" width="48" height="48"></a>')
print('<h4>')
print(branding_print_banner())
print('</h4>')
print('</div>')

print('<ol class="breadcrumb">')
print('<li><a href="xtendweb.cgi"><span class="glyphicon glyphicon-repeat"></span></a></li>')
print('<li class="active">Server Config</li>')
print('</ol>')

# Check if backup config file is present or initilize otherwise
if os.path.isfile(backup_config_file):
    # Get all config settings from the backup config file
    with open(backup_config_file, 'r') as backup_config_file_stream:
        yaml_parsed_backupyaml = yaml.safe_load(backup_config_file_stream)
    # Backup settings
    pkgacct_backup = yaml_parsed_backupyaml.get('pkgacct_backup')
    system_files = yaml_parsed_backupyaml.get('system_files')
    mysql_backup = yaml_parsed_backupyaml.get('mysql_backup')
    backup_path = yaml_parsed_backupyaml.get('backup_path')
else:
    pkgacct_backup = "enabled"
    system_files = "enabled"
    mysql_backup = "enabled"
    backup_path = "/backup"
    backup_config_dict = {"pkgacct_backup": "enabled", "system_files": "enabled", "mysql_backup": "enabled", "backup_path": "/backup"}
    with open(backup_config_file, 'w') as backup_config_file_stream:
        yaml.dump(backup_config_dict, backup_config_file_stream, default_flow_style=False)
if not os.path.isfile('/opt/nDeploy/scripts/borgmatic_cpanel_backup_hook.sh'):
    # We create the borgmatic hook now
    # Initiate Jinja2 templateEnv
    templateLoader = jinja2.FileSystemLoader(installation_path + "/conf/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templateVars = {"BACKUP_PATH": backup_path,
                    "PKGACCT_BACKUP": pkgacct_backup,
                    "SYSTEM_FILES": system_files,
                    "MYSQL_BACKUP": mysql_backup
                    }
    borgmatic_hook_template = templateEnv.get_template("borgmatic_cpanel_backup_hook.sh.j2")
    borgmatic_hook_script = borgmatic_hook_template.render(templateVars)
    with codecs.open('/opt/nDeploy/scripts/borgmatic_cpanel_backup_hook.sh', 'w', 'utf-8') as borgmatic_hook_myscript:
        borgmatic_hook_myscript.write(borgmatic_hook_script)
    os.chmod("/opt/nDeploy/scripts/borgmatic_cpanel_backup_hook.sh", 0o755)
# Next section start here
print('<div class="panel panel-default">')  # default
print(('<div class="panel-heading" role="tab" id="headingOne"><h3 class="panel-title"><a role="button" data-toggle="collapse" data-parent="#accordion" href="#collapseOne" aria-expanded="false" aria-controls="collapseOne">BACKUP SETTINGS</a></h3></div>'))  # heading
print('<div id="collapseOne" class="panel-collapse collapse" role="tabpanel" aria-labelledby="headingOne">')  # collapse
print('<div class="panel-body">')  # body
print('<form id="config" class="form-inline" action="save_backup_settings.cgi" method="post">')

print('<ul class="list-group">')

# system_files
print('<li class="list-group-item">')
system_files_hint = "Backup cPanel system files"
print('<div class="row">')
if system_files == 'enabled':
    print_green("system_files", system_files_hint)
    print('<div class="col-sm-6 col-radio">')
    print('<div class="radio"><label><input type="radio" name="system_files" value="enabled" checked/> Enabled</label></div>')
    print('<div class="radio"><label><input type="radio" name="system_files" value="disabled" /> Disabled</label></div>')
    print('</div>')
else:
    print_red("system_files", system_files_hint)
    print('<div class="col-sm-6 col-radio">')
    print('<div class="radio"><label><input type="radio" name="system_files" value="enabled" /> Enabled</label></div>')
    print('<div class="radio"><label><input type="radio" name="system_files" value="disabled" checked/> Disabled</label></div>')
    print('</div>')
    print('</div>')
    print('</li>')
# mysql_backup
print('<li class="list-group-item">')
print('<div class="row">')
mysql_backup_hint = "Use MariaBackup to backup full MySQL datadir"
if mysql_backup == 'enabled':
    print_green("mysql_backup", mysql_backup_hint)
    print('<div class="col-sm-6 col-radio">')
    print('<div class="radio"><label><input type="radio" name="mysql_backup" value="enabled" checked/> Enabled</label></div>')
    print('<div class="radio"><label><input type="radio" name="mysql_backup" value="disabled" /> Disabled</label></div>')
    print('</div>')
else:
    print_red("mysql_backup", mysql_backup_hint)
    print('<div class="col-sm-6 col-radio">')
    print('<div class="radio"><label><input type="radio" name="mysql_backup" value="enabled" /> Enabled</label></div>')
    print('<div class="radio"><label><input type="radio" name="mysql_backup" value="disabled" checked/> Disabled</label></div>')
    print('</div>')
    print('</div>')
    print('</li>')
# backup_path
print('<li class="list-group-item">')
print('<div class="row">')
backup_path_hint = "The directory where the cPanel pkgacct,MySQL backup and system files are stored"
print_green("Backup Target Dir", backup_path_hint)
print('<div class="col-sm-6 col-radio">')
# print('<div class="alert alert-info">The path where you want pkgacct,MySQL and system backups stored: </div>')
print('<input class="form-control" placeholder="'+backup_path+'" type="text" name="backup_path">')
print('</div>')
print('</li>')

print('</ul>')

print('<input class="btn btn-primary" type="submit" value="Submit">')

print('</form>')
print('</div>')  # body
print('</div>')  # collapse
print('</div>')  # default

# Check if borgmatic config file is present or initilize otherwise
if not os.path.isfile(borgmatic_config_file):
    # We create the borgmatic config now
    # Initiate Jinja2 templateEnv
    templateLoader = jinja2.FileSystemLoader(installation_path + "/conf/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templateVars = {"BACKUP_PATH": backup_path}
    borgmatic_conf_template = templateEnv.get_template("borgmatic_sample_config.yaml.j2")
    borgmatic_conf = borgmatic_conf_template.render(templateVars)
    with codecs.open(borgmatic_config_file, 'w', 'utf-8') as borgmatic_conf_file:
        borgmatic_conf_file.write(borgmatic_conf)

# Since we have a borgmatic config now.Lets load it up and present to the user
if os.path.isfile(borgmatic_config_file):
    # Get all config settings from the borgmatic config file
    with open(borgmatic_config_file, 'r') as borgmatic_config_file_stream:
        yaml_parsed_borgmaticyaml = yaml.safe_load(borgmatic_config_file_stream)
    # borgmatic sections
    borgmatic_location = yaml_parsed_borgmaticyaml.get('location')
    borgmatic_storage = yaml_parsed_borgmaticyaml.get('storage')
    borgmatic_retention = yaml_parsed_borgmaticyaml.get('retention')
    repositories = borgmatic_location['repositories'][0]
    remote_rate_limit = borgmatic_storage['remote_rate_limit']
    ssh_command = borgmatic_storage['ssh_command']

# Lets present the borgmatic config to the user
# Next section start here
print('<div class="panel panel-default">')  # default
print(('<div class="panel-heading" role="tab" id="headingTwo"><h3 class="panel-title"><a role="button" data-toggle="collapse" data-parent="#accordion" href="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">BORG SETTINGS</a></h3></div>'))  # heading
print('<div id="collapseTwo" class="panel-collapse collapse" role="tabpanel" aria-labelledby="headingTwo">')  # collapse
print('<div class="panel-body">')  # body
print('<form id="config" class="form-inline" action="save_borgmatic_settings.cgi" method="post">')

print('<ul class="list-group">')

# repositories
print('<li class="list-group-item">')
print('<div class="row">')
repositories_hint = "eg: user@backupserver:sourcehostname.borg"
print_green("repositories", repositories_hint)
print('<div class="col-sm-6 col-radio">')
print('<input class="form-control" placeholder="'+repositories+'" type="text" name="repositories">')
print('</div>')
print('</li>')

# remote_rate_limit
print('<li class="list-group-item">')
print('<div class="row">')
remote_rate_limit_hint = "network upload rate limit in kiBytes/second"
print_green("network rate limit", remote_rate_limit_hint)
print('<div class="col-sm-6 col-radio">')
print('<input class="form-control" placeholder="'+str(remote_rate_limit)+'" type="text" name="remote_rate_limit">')
print('</div>')
print('</li>')

# ssh_command
print('<li class="list-group-item">')
print('<div class="row">')
ssh_command_hint = "options for ssh"
print_green("ssh_command", ssh_command_hint)
print('<div class="col-sm-6 col-radio">')
print('<input class="form-control" placeholder="'+ssh_command+'" type="text" name="ssh_command">')
print('</div>')
print('</li>')

print('</ul>')

print('<input class="btn btn-primary" type="submit" value="Submit">')

print('</form>')
print('</div>')  # body
print('</div>')  # collapse
print('</div>')  # default

print('<div class="panel-footer"><small>')
print(branding_print_footer())
print('</small></div>')

print('</div>')  # marker3
print('</div>')  # marker2
print('</body>')
print('</html>')
