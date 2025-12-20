{
  description = "Example: Using auto-updated WeChat";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    
    wechat-auto-update = {
      url = "github:Aozora-Wings/wechat-auto-update";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        wechat-monitor = {
          url = "github:Aozora-Wings/wechat-linux-monitor";
          flake = false;
        };
      };
    };
  };

  outputs = { self, nixpkgs, wechat-auto-update, ... }:
    {
      nixosConfigurations.example = nixpkgs.lib.nixosSystem {
        modules = [
          wechat-auto-update.nixosModules.default
          ./configuration.nix
        ];
      };
    };
}