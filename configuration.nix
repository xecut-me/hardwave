
{ config, pkgs, lib, ... }:

let
  credentials = import ./credentials.nix;

  queryValue = value:
    if builtins.isList value
    then lib.concatMapStringsSep "," toString value
    else toString value;

  hardwaveUrl =
    credentials.kioskUrl or
      "https://hardwave.tgr.rs/index.html?api_key=${credentials.telegramBotToken}&chat_id=${queryValue credentials.telegramChatId}&admin_ids=${queryValue credentials.telegramAdminIds}";

  waitForX = pkgs.writeShellScript "hardwave-wait-for-x" ''
    for i in $(${pkgs.coreutils}/bin/seq 1 100); do
      ${pkgs.xorg.xset}/bin/xset q >/dev/null 2>&1 && exit 0
      ${pkgs.coreutils}/bin/sleep 0.1
    done

    exit 1
  '';

  configureDisplay = pkgs.writeShellScript "hardwave-configure-display" ''
    ${pkgs.xorg.xset}/bin/xset s off -dpms s noblank
    ${pkgs.xorg.xrandr}/bin/xrandr --output eDP1 --rotate left || true
  '';

  kioskSession = pkgs.writeShellScript "hardwave-kiosk-session" ''
    ${pkgs.openbox}/bin/openbox-session &

    exec ${pkgs.chromium}/bin/chromium \
      --no-sandbox \
      --kiosk \
      --no-first-run \
      --disable-infobars \
      --noerrdialogs \
      --use-fake-ui-for-media-stream \
      --remote-debugging-port=9222 \
      --enable-features=WebHID \
      --disable-features=WebHIDBlocklist \
      --auto-accept-this-tab-capture \
      --enable-experimental-web-platform-features \
      --user-data-dir="$HOME/.config/chromium-kiosk" \
      ${lib.escapeShellArg hardwaveUrl}
  '';
in
{
  imports = [ ./hardware-configuration.nix ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.kernelParams = [ "nohibernate" ];

  networking.hostName = "hardware";

  networking.networkmanager = {
    enable = true;

    ensureProfiles.profiles.xecut = {
      connection = { id = "xecut"; type = "wifi"; interface-name = "wlp1s0"; autoconnect = true; };
      wifi = { mode = "infrastructure"; ssid = "xecut"; };
      wifi-security = { auth-alg = "open"; key-mgmt = "sae"; psk = credentials.wifiPassword; };
      ipv4.method = "auto";
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
  users.groups.kiosk = { };
  users.users.root = {
    hashedPassword = lib.mkForce null;
    password = credentials.rootPassword;
    openssh.authorizedKeys.keys = [ credentials.sshKey ];
  };
  users.users.kiosk = {
    isNormalUser = true;
    group = "kiosk";
    home = "/home/kiosk";
    createHome = true;
    shell = pkgs.bashInteractive;
    extraGroups = [ "input" "video" ];
  };

  services.getty.helpLine = ''
    Hardwave kiosk is managed by systemd.
    Status: systemctl status hardwave-kiosk
    Logs: journalctl -u hardwave-kiosk -f
  '';

  services.xserver = {
    enable = true;
    windowManager.openbox.enable = true;
  };

  systemd.tmpfiles.rules = [
    "d /home/kiosk/logs 0755 kiosk kiosk -"
    "d /home/kiosk/.config 0755 kiosk kiosk -"
    "d /home/kiosk/.config/chromium-kiosk 0755 kiosk kiosk -"
  ];

  systemd.services.hardwave-xorg = {
    description = "Hardwave Xorg server";
    wantedBy = [ "multi-user.target" ];
    conflicts = [ "getty@tty1.service" ];
    before = [ "hardwave-kiosk.service" ];

    serviceConfig = {
      ExecStart = "${pkgs.xorg.xorgserver}/bin/Xorg :0 vt1 -keeptty -nolisten tcp -noreset -ac";
      Restart = "always";
      RestartSec = 2;
      StandardInput = "tty";
      StandardOutput = "journal";
      StandardError = "journal";
      TTYPath = "/dev/tty1";
      TTYReset = true;
      TTYVHangup = true;
      TTYVTDisallocate = true;
    };
  };

  systemd.services.hardwave-kiosk = {
    description = "Hardwave Chromium kiosk";
    wantedBy = [ "multi-user.target" ];
    after = [ "systemd-user-sessions.service" "network-online.target" "hardwave-xorg.service" ];
    wants = [ "network-online.target" "hardwave-xorg.service" ];
    requires = [ "hardwave-xorg.service" ];

    environment = {
      DISPLAY = ":0";
      HOME = "/home/kiosk";
      USER = "kiosk";
      LOGNAME = "kiosk";
    };

    serviceConfig = {
      User = "kiosk";
      Group = "kiosk";
      ExecStartPre = [
        waitForX
        configureDisplay
      ];
      ExecStart = "${pkgs.dbus}/bin/dbus-run-session --dbus-daemon=${pkgs.dbus}/bin/dbus-daemon ${kioskSession}";
      Restart = "always";
      RestartSec = 2;
      WorkingDirectory = "/home/kiosk";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  environment.etc."X11/xorg.conf.d/10-monitor.conf".text = ''
    Section "Monitor"
        Identifier "Monitor0"
        Option "DPMS" "false"
    EndSection

    Section "ServerFlags"
        Option "BlankTime" "0"
        Option "StandbyTime" "0"
        Option "SuspendTime" "0"
        Option "OffTime" "0"
    EndSection
  '';

  environment.etc."chromium/policies/managed/webhid.json".text = builtins.toJSON {
    DefaultWebHidGuardSetting = 1;
    WebHidAllowAllDevicesForUrls = [ "https://hardwave.tgr.rs/" ];
    WebHidAskForUrls = [ "https://hardwave.tgr.rs/" ];
  };

  services.udev.extraRules = ''
    KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="239a", ATTRS{idProduct}=="80b4", MODE="0660", GROUP="kiosk"
  '';

  systemd.targets.sleep.enable = false;
  systemd.targets.suspend.enable = false;
  systemd.targets.hibernate.enable = false;
  systemd.targets.hybrid-sleep.enable = false;

  environment.systemPackages = with pkgs; [
    chromium
    curl
    git
    htop
    openbox
    tmux
    vim
    xorg.xrandr
    xorg.xorgserver
    xorg.xset
  ];

  system.stateVersion = "26.05";
}
