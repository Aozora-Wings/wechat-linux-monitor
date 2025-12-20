{ config, pkgs, ... }:

{
  # 启用自动更新的 WeChat
  programs.wechat-auto-update.enable = true;
  
  # 现在 wechat 会自动使用最新版本
  environment.systemPackages = with pkgs; [
    wechat
  ];
  
  # 可选：添加更新提醒服务
  systemd.services.wechat-update-notify = {
    description = "Check for WeChat updates";
    serviceConfig.Type = "oneshot";
    script = ''
      ${pkgs.writeScriptBin "check-update" ''
        #!/bin/sh
        CURRENT="$(${pkgs.nix}/bin/nix eval --raw .#wechat.version)"
        LATEST="$(${pkgs.curl}/bin/curl -s https://raw.githubusercontent.com/Aozora-Wings/wechat-linux-monitor/main/data/last_release_version.txt)"
        
        if [ "$CURRENT" != "$LATEST" ]; then
          echo "WeChat update available: $CURRENT -> $LATEST"
          echo "Run: sudo nix flake update && sudo nixos-rebuild switch"
        fi
      ''}/bin/check-update
    '';
  };
  
  systemd.timers.wechat-update-notify = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
    };
  };
}