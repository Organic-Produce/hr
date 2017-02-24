Vagrant.configure("2") do |config|
  config.vm.box = "clock"
  config.ssh.username = "clock"

  config.vm.hostname = "clock.local"

  ## For masterless, mount your salt file root
  config.vm.synced_folder ".", "/vagrant", :nfs=>true

  config.vm.synced_folder "salt/", "/srv/salt/", :nfs=>true
  config.vm.synced_folder "salt/src/", "/home/clock/src/", :nfs=>true

  config.vm.network "private_network", ip: "172.16.81.150"

  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 5432, host: 54324
  config.vm.network "forwarded_port", guest: 9200, host: 9209

  # raising memory allocation for vm
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--memory", "1024"]
  end

  config.vm.provision :salt do |salt|
    salt.minion_config = "minion"
  end
end
