# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.

Vagrant.require_version ">= 1.9.1"

Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/xenial64"

  # do not update configured box
  # config.vm.box_check_update = false

  # user insecure key
  # config.ssh.insert_key = false

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false
  # enable ssh agent forwarding
  config.ssh.forward_agent = true

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:

  config.vm.define "keras-on-aws", autostart: true do |machine|
    machine.vm.provider "virtualbox" do |vb|
      # vb.gui = true
      vb.memory = "2048"
      vb.cpus = "1"

      if Vagrant::Util::Platform.windows? then
        # Fix for slow external network connections for Windows 10
        vb.customize ['modifyvm', :id, '--natdnshostresolver1', 'on']
        vb.customize ['modifyvm', :id, '--natdnsproxy1', 'on']
      end
    end

#     if Vagrant::Util::Platform.windows? then
#         machine.vm.network "public_network"
#     else
#         # Linux machine with Docker has multiple network interfaces
#         machine.vm.network "public_network", bridge: "eth0"
#     end

    machine.vm.hostname = "keras-on-aws"
    machine.vm.network "private_network", ip: "192.168.33.10"

    machine.vm.provision "ansible_local" do |ansible|
      ansible.install_mode = "pip"
      ansible.version = "2.2.3.0"
      ansible.provisioning_path = "/vagrant/ansible/local"
      ansible.galaxy_role_file = "requirements.yml"
      ansible.galaxy_roles_path = "/vagrant/ansible/external-roles"
      ansible.playbook = "playbook.yml"
    end
  end
end
