
{ config, pkgs, lib, ... }:

let
  credentials = import ./credentials.nix;
in
{
  imports =
    [ 
      ./hardware-configuration.nix
    ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "nixos"; # Define your hostname.

  networking.networkmanager = {
    enable = true;

    ensureProfiles.profiles.xecut = {
      connection = {
        id = "xecut";
        type = "wifi";
        interface-name = "wlp1s0";
        autoconnect = true;
      };

      wifi = {
        mode = "infrastructure";
        ssid = "xecut";
      };

      wifi-security = {
        auth-alg = "open";
        key-mgmt = "sae";
        psk = credentials.wifiPassword;
      };

      ipv4.method = "auto";

      ipv6 = {
        addr-gen-mode = "default";
        method = "auto";
      };
    };
  };

  time.timeZone = "Europe/Belgrade";
  i18n.defaultLocale = "en_US.UTF-8";

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
    password = credentials.rootPassword;
    openssh.authorizedKeys.keys = [ credentials.sshKey ];
  };

  environment.systemPackages = with pkgs; [ vim curl git ];

  system.stateVersion = "26.05";
}
