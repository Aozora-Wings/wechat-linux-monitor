{
  description = "Auto-updated WeChat overlay";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    
    wechat-monitor = {
      url = "github:Aozora-Wings/wechat-linux-monitor";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, wechat-monitor }:
    let
      # 读取最新版本
      version = nixpkgs.lib.removeSuffix "\n" (builtins.readFile "${wechat-monitor}/data/last_release_version.txt");
      
      # 读取哈希数据
      versionsData = builtins.fromJSON (builtins.readFile "${wechat-monitor}/data/versions.json");
      versionEntry = builtins.head (builtins.filter (v: v.version == version) versionsData.versions);
      
      # 获取哈希值的函数
      getHash = arch: pkgType:
        versionEntry.architectures.${arch}.${pkgType}.hash;
      
      # 创建 overlay
      overlay = final: prev: {
        wechat = prev.wechat.overrideAttrs (oldAttrs:
          # 只覆盖 Linux 版本
          if prev.stdenvNoCC.hostPlatform.isLinux then
            let
              system = prev.stdenvNoCC.hostPlatform.system;
              arch = if system == "x86_64-linux" then "x86"
                    else if system == "aarch64-linux" then "arm64"
                    else throw "Unsupported Linux system: ${system}";
              
              # 使用 AppImage 版本
              pkgType = "appimage";
              extension = "AppImage";
              filename = "wechat_linux_${arch}_${version}.${extension}";
            in
            {
              version = version;
              
              src = prev.fetchurl {
                url = "https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v${version}/${filename}";
                sha256 = getHash arch pkgType;
              };
              
              # 保持其他所有属性不变
            }
          else
            oldAttrs  # macOS 保持不变
        );
      };
      
      # 支持的系统
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      
      # 为每个系统生成包
      forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: 
        f nixpkgs.legacyPackages.${system});
      
    in
    {
      # 主要输出：overlay
      overlays.default = overlay;
      
      # NixOS 模块（简单封装）
      nixosModules.default = { config, pkgs, ... }:
        let
          inherit (nixpkgs.lib) mkOption types mkIf;
        in
        {
          options.programs.wechat-auto-update = {
            enable = mkOption {
              type = types.bool;
              default = false;
              description = ''
                Enable auto-updated WeChat package.
                This will apply an overlay that updates WeChat to the latest version
                from the monitoring repository.
              '';
            };
          };
          
          config = mkIf config.programs.wechat-auto-update.enable {
            nixpkgs.overlays = [ overlay ];
          };
        };
      
      # Home Manager 模块
      homeManagerModules.default = { config, pkgs, ... }:
        let
          inherit (nixpkgs.lib) mkOption types mkIf;
        in
        {
          options.programs.wechat-auto-update = {
            enable = mkOption {
              type = types.bool;
              default = false;
              description = "Enable auto-updated WeChat for Home Manager";
            };
          };
          
          config = mkIf config.programs.wechat-auto-update.enable {
            nixpkgs.overlays = [ overlay ];
          };
        };
      
      # 导出检查工具（可选）
      apps = forAllSystems (pkgs: {
        check-wechat-version = {
          type = "app";
          program = toString (pkgs.writeScriptBin "check-wechat-version" ''
            #!/bin/sh
            echo "Current WeChat version in overlay: ${version}"
            echo "Original WeChat version in nixpkgs: ${pkgs.wechat.version}"
            
            if [ "${version}" != "${pkgs.wechat.version}" ]; then
              echo "⚠️  New version available!"
              echo "Run: nix flake update"
            else
              echo "✓ Up to date"
            fi
          '');
        };
        
        default = self.apps.${pkgs.system}.check-wechat-version;
      });
      
      # 模板示例
      templates.default = {
        path = ./template;
        description = "Example configuration using auto-updated WeChat";
      };
    };
}