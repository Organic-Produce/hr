Vagrant.configure("2") do |config|
  config.vm.box = "clock"
  config.ssh.username = "clock"

  config.vm.hostname = "clock.local"

  ## For masterless, mount your salt file root
  config.vm.synced_folder ".", "/vagrant", :nfs=>true
  config.vm.synced_folder "salt/", "/srv/salt/", :nfs=>true
  config.vm.synced_folder "salt/src/app", "/home/clock/src/app", :nfs=>true

  config.vm.network "private_network", ip: "172.16.81.150", adapter: 3

  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 5432, host: 54324
  config.vm.network "forwarded_port", guest: 9200, host: 9209

  config.vm.network "public_network", adapter: 2, :bridge => 'wlan0'

  # raising memory allocation for vm
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", "2048"]
#    vb.gui = true
  end

  config.vm.boot_timeout = 12000

  config.vm.provision :salt do |salt|
    salt.minion_config = "minion"
  end
end
