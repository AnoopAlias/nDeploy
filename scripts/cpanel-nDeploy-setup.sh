#!/bin/bash
# Author: Anoop P Alias

function enable {
echo -e '\e[93m Generating the default nginx vhosts \e[0m'
python /opt/nDeploy/scripts/generate_default_vhost_config.py
echo -e '\e[93m Modifying apache http and https port in cpanel \e[0m'
/usr/local/cpanel/bin/whmapi1 set_tweaksetting key=apache_port value=0.0.0.0:9999
/usr/local/cpanel/bin/whmapi1 set_tweaksetting key=apache_ssl_port value=0.0.0.0:4430
sed -i "s/80/9999/" /etc/chkserv.d/httpd
/opt/nDeploy/scripts/attempt_autofix.sh
service tailwatchd restart
if [ -f /etc/cpanel/ea4/is_ea4 ];then
	echo -e '\e[93m !!! Removing conflicting ea-apache24-mod_ruid2 ea-apache24-mod_http2 rpm \e[0m'
	yum -y remove ea-apache24-mod_ruid2 ea-apache24-mod_http2
	yum -y install ea-apache24-mod_remoteip
	REMOTEIPINCLUDE=$'\nInclude "/etc/nginx/conf.d/httpd_mod_remoteip.include"'
	grep "httpd_mod_remoteip.include" /etc/apache2/conf.d/includes/pre_virtualhost_global.conf || echo ${REMOTEIPINCLUDE} >> /etc/apache2/conf.d/includes/pre_virtualhost_global.conf
fi
echo -e '\e[93m Rebuilding Apache httpd backend configs and restarting daemons \e[0m'
/scripts/rebuildhttpdconf
/scripts/restartsrv httpd
osversion=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+'|cut -d"." -f1)
if [ ${osversion} -le 6 ];then
	service nginx restart
	service ndeploy_watcher restart
	service ndeploy_backends restart
	chkconfig nginx on
	chkconfig ndeploy_watcher on
	chkconfig ndeploy_backends on
else
	# test for OpenVZ/Virtuozzo platform
	/usr/sbin/sysctl -w net.core.somaxconn=16384
	if [ $? -ne 0 ];then
		sed 's/^ExecStartPre=\/usr\/sbin\/sysctl/#ExecStartPre=\/usr\/sbin\/sysctl/' /usr/lib/systemd/system/nginx.service > /etc/systemd/system/nginx.service
		systemctl daemon-reload
	fi
	/usr/sbin/sysctl -w net.core.netdev_max_backlog=16384
	if [ $? -ne 0 ];then
		sed 's/^ExecStartPre=\/usr\/sbin\/sysctl/#ExecStartPre=\/usr\/sbin\/sysctl/' /usr/lib/systemd/system/nginx.service > /etc/systemd/system/nginx.service
		systemctl daemon-reload
	fi
	systemctl restart nginx
	systemctl restart ndeploy_watcher
	systemctl restart ndeploy_backends
	systemctl enable nginx
	systemctl enable ndeploy_watcher
	systemctl enable ndeploy_backends
fi

}

function disable {

echo -e '\e[93m Reverting apache http and https port in cpanel \e[0m'
/usr/local/cpanel/bin/whmapi1 set_tweaksetting key=apache_port value=0.0.0.0:80
/usr/local/cpanel/bin/whmapi1 set_tweaksetting key=apache_ssl_port value=0.0.0.0:443
sed -i "s/9999/80/" /etc/chkserv.d/httpd

service tailwatchd restart

echo -e '\e[93m Rebuilding Apache httpd backend configs.Apache will listen on default ports!  \e[0m'
osversion=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+'|cut -d"." -f1)
if [ ${osversion} -le 6 ];then
	service nginx stop
	service ndeploy_watcher stop
	service ndeploy_backends stop
	chkconfig nginx off
	chkconfig ndeploy_watcher off
	chkconfig ndeploy_backends off
else
	systemctl stop nginx
	systemctl stop ndeploy_watcher
	systemctl stop ndeploy_backends
	systemctl disable nginx
	systemctl disable ndeploy_watcher
	systemctl disable ndeploy_backends
fi
/scripts/rebuildhttpdconf
/scripts/restartsrv httpd

}


case "$1" in
        enable)
            enable
            ;;

        disable)
            disable
            ;;
        *)
            echo $"Usage: $0 {enable|disable}"
            exit 1

esac
