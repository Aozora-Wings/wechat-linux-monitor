#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import hashlib
from datetime import datetime

def download_and_hash(url, filename):
    """下载文件并计算SHA256哈希值"""
    try:
        print(f"下载: {filename}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 计算哈希值
        sha256_hash = hashlib.sha256()
        size = 0
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    sha256_hash.update(chunk)
                    size += len(chunk)
        
        return sha256_hash.hexdigest(), size
    except Exception as e:
        print(f"下载 {filename} 失败: {e}")
        return "", 0

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
    
    # 定义要下载的文件
    files_to_download = [
        ("x86", "deb", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.deb"),
        ("x86", "rpm", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.rpm"),
        ("x86", "appimage", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.AppImage"),
        ("arm64", "deb", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.deb"),
        ("arm64", "rpm", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.rpm"),
        ("arm64", "appimage", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.AppImage"),
        ("loongarch", "deb", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_LoongArch.deb")
    ]
    
    # 初始化文件数据结构
    files_data = {
        "x86": {"deb": {}, "rpm": {}, "appimage": {}},
        "arm64": {"deb": {}, "rpm": {}, "appimage": {}},
        "loongarch": {"deb": {}}
    }
    
    # 下载文件并计算哈希
    for arch, pkg_type, url in files_to_download:
        filename = f"wechat_linux_{arch}_{version}.{pkg_type}"
        sha256, size = download_and_hash(url, filename)
        
        files_data[arch][pkg_type] = {
            "filename": filename,
            "sha256": sha256,
            "size": size,
            "url": url,
            "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/{filename}"
        }
    
    # 创建版本数据结构
    new_version_data = {
        "version": version,
        "timestamp": current_time,
        "files": files_data
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
    existing_version_index = None
    for i, v in enumerate(data.get('versions', [])):
        if v['version'] == version:
            existing_version_index = i
            break
    
    if existing_version_index is not None:
        # 版本已存在，检查是否需要更新哈希值
        existing_version = data['versions'][existing_version_index]
        has_empty_hashes = any(
            file_info.get('sha256', '') == '' 
            for arch_files in existing_version.get('files', {}).values()
            for file_info in arch_files.values()
        )
        
        if has_empty_hashes:
            # 更新现有版本的数据
            data['versions'][existing_version_index] = new_version_data
            print(f"更新版本 {version} 的哈希值")
        else:
            print(f"版本 {version} 已存在且哈希值完整")
            return False
    else:
        # 添加新版本
        data['versions'] = data.get('versions', []) + [new_version_data]
        print(f"新版本发现: {version}")
    
    data['latest_version'] = version
    data['last_checked'] = current_time
    
    # 保存数据
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return True

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