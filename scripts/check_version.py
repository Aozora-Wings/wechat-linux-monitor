#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

def get_current_version():
    """获取当前页面显示的版本号"""
    try:
        url = "https://linux.weixin.qq.com"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找版本号
        version_element = soup.select_one('#__nuxt > div > div > div.main-section__bd > div.main-section__bd-version')
        
        if version_element:
            version_text = version_element.text.strip()
            match = re.search(r'(\d+\.\d+\.\d+)', version_text)
            if match:
                return match.group(1)
        
        # 备用方案
        for element in soup.find_all(text=re.compile(r'\d+\.\d+\.\d+')):
            match = re.search(r'(\d+\.\d+\.\d+)', element)
            if match:
                return match.group(1)
                
        return None
        
    except Exception as e:
        print(f"获取版本失败: {e}")
        return None

def update_version_data(version):
    """更新版本数据文件"""
    data_file = "data/versions.json"
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # 基础版本数据结构（哈希值会在 workflow 中填充）
    new_version_data = {
        "version": version,
        "timestamp": current_time,
        "files": {
            "x86": {
                "deb": {
                    "filename": f"wechat_linux_x86_{version}.deb",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.deb",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_x86_{version}.deb"
                },
                "rpm": {
                    "filename": f"wechat_linux_x86_{version}.rpm",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.rpm",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_x86_{version}.rpm"
                },
                "appimage": {
                    "filename": f"wechat_linux_x86_{version}.AppImage",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.AppImage",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_x86_{version}.AppImage"
                }
            },
            "arm64": {
                "deb": {
                    "filename": f"wechat_linux_arm64_{version}.deb",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.deb",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_arm64_{version}.deb"
                },
                "rpm": {
                    "filename": f"wechat_linux_arm64_{version}.rpm",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.rpm",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_arm64_{version}.rpm"
                },
                "appimage": {
                    "filename": f"wechat_linux_arm64_{version}.AppImage",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.AppImage",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_arm64_{version}.AppImage"
                }
            },
            "loongarch": {
                "deb": {
                    "filename": f"wechat_linux_loongarch_{version}.deb",
                    "sha256": "",
                    "size": 0,
                    "url": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_LoongArch.deb",
                    "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/wechat_linux_loongarch_{version}.deb"
                }
            }
        }
    }
    
    # 加载或创建数据
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "versions": [],
            "latest_version": "",
            "last_checked": ""
        }
    
    # 检查版本是否已存在
    version_exists = any(v['version'] == version for v in data.get('versions', []))
    
    if not version_exists:
        # 添加新版本
        data['versions'] = data.get('versions', []) + [new_version_data]
        data['latest_version'] = version
        data['last_checked'] = current_time
        
        # 保存数据
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"新版本发现: {version}")
        return True
    else:
        print(f"版本 {version} 已存在")
        return False

def main():
    version = get_current_version()
    
    if not version:
        print("无法获取版本号")
        return
    
    print(f"检测到版本: {version}")
    
    # 更新版本数据
    update_version_data(version)

if __name__ == "__main__":
    main()