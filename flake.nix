{
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11"; };

  outputs = { self, nixpkgs }:
  let
    credentials = import ./credentials.nix;

    lib = nixpkgs.lib;
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    common = { config, lib, pkgs, ... }: {
      time.timeZone = "Europe/Belgrade";
      i18n.defaultLocale = "en_US.UTF-8";

      nix.settings.experimental-features = [ "nix-command" "flakes" ];

      networking.hostName = "hardwave";
      networking.firewall.enable = true;
      networking.networkmanager = {
        enable = true;
        ensureProfiles.profiles.xecut = {
          connection = {
            id = "xecut";
            type = "wifi";
            autoconnect = true;
          };

          wifi = {
            mode = "infrastructure";
            ssid = "xecut";
          };

          wifi-security = {
            key-mgmt = "sae";
            pmf = 2;
            psk = credentials.wifiPassword;
          };

          ipv4.method = "auto";
          ipv6.method = "auto";
        };
      };

      hardware.enableRedistributableFirmware = true;

      boot.extraModulePackages = [ config.boot.kernelPackages.rtl8821ce ];
      boot.kernelModules = [ "8821ce" ];
      boot.initrd.availableKernelModules = [ "8821ce" ];
      
      services.openssh = {
        enable = true;

        settings = {
          PasswordAuthentication = false;
          KbdInteractiveAuthentication = false;
          PermitRootLogin = "prohibit-password";
          X11Forwarding = false;
          AllowUsers = [ "root" ];
        };
      };

      users.mutableUsers = false;
      users.users.root = {
        hashedPassword = lib.mkForce null;
        password = "root";
        openssh.authorizedKeys.keys = [ credentials.sshKey ];
      };

      environment.systemPackages = with pkgs; [
        vim curl openssl htop tmux pciutils usbutils lsof iotop ethtool ipmitool smartmontools nvme-cli
      ];

      systemd.targets.sleep.enable = false;
      systemd.targets.suspend.enable = false;
      systemd.targets.hibernate.enable = false;
      systemd.targets.hybrid-sleep.enable = false;

      system.stateVersion = "25.11";
    };

    live = lib.nixosSystem {
      inherit system;

      modules = [
        common

        ({ config, lib, pkgs, modulesPath, ... }: {
          imports = [ "${modulesPath}/installer/cd-dvd/installation-cd-minimal.nix" ];
        })
      ];
    };

    switch = lib.nixosSystem {
      inherit system;

      modules = [
        common

        ({ modulesPath, ... }: {
          imports = [ "${modulesPath}/profiles/minimal.nix" ];
          boot.kernelParams = [ "nohibernate" ];
        })
      ];
    };

    efi = lib.nixosSystem {
      inherit system;

      modules = [
        common

        ({ config, lib, modulesPath, ... }: {
          imports = [ "${modulesPath}/installer/netboot/netboot.nix" "${modulesPath}/profiles/minimal.nix" ];
          boot.kernelParams = [ "nohibernate" ];

          boot.uki.name = "ephemeral";
          boot.uki.version = null;
          boot.uki.settings.UKI.Initrd = lib.mkForce "${config.system.build.netbootRamdisk}/initrd";
        })
      ];
    };
  in
  {
    nixosConfigurations = { inherit live; inherit switch; inherit efi; };

    packages.${system} = {
      live = live.config.system.build.isoImage;
      switch = switch.config.system.build.toplevel;
      efi = efi.config.system.build.uki;
    };
  };
}
