
# https://www.homeautomationguy.io/home-assistant-tips/installing-docker-home-assistant-and-portainer-on-ubuntu-linux/
# https://www.homeautomationguy.io/home-assistant-tips/using-visual-studio-to-edit-your-home-assistant-configuration-yaml-file-over-ssh/
# https://www.homeautomationguy.io/docker-tips/accessing-usb-devices-from-docker-containers/
# https://www.homeautomationguy.io/youtube-videos/living-without-add-ons-on-home-assistant-container/
# https://www.homeautomationguy.io/docker-tips/configuring-the-mosquitto-mqtt-docker-container-for-use-with-home-assistant/

ssh:
	ssh -L 9000:localhost:9000 -L 5432:localhost:5432 -L 8123:localhost:8123 -L 8200:localhost:8200 -L 1883:localhost:1883 odroid@odroid

## ssh ha-odroid
#Host ha-odroid
#  HostName 10.0.1.3
#  User odroid
#  IdentityFile ~/.ssh/id_rsa
#  Port 22
#
#  ## sample for ProxyJump
#  ProxyJump vagrant@v2202206177879193164.goodsrv.de
#
#  ## sample for ProxyCommand
#  ProxyCommand ssh -W %h:%p v2202206177879193164.goodsrv.de
ha-odroid:
	ssh -L 9000:localhost:9000  ha-odroid

ansible_ping:
	ansible all -m ping

deploy:
	ansible-playbook setup.yml --ask-become-pass

deploy_:
	ansible-playbook setup.yml -e "ansible_become_pass=yourPassword"

# local: ~/.ssh/config
#Host odroid-root
#  HostName 127.0.0.1
#  ProxyJump odroid@odroid
#  User root
# remote: /etc/ssh/sshd_config
#Match Address 127.0.0.1
#        PermitRootLogin yes
# remote /root/.ssh/authorized_keys
backup:
	rsync -av --links --progress --stats --exclude "*.log*" --exclude "*.db" --exclude ".storage" --exclude ".cloud" odroid-root:/opt/homeassistant/data/homeassistant/config ./homeassistant-backup
