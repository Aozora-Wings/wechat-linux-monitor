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

def check_version_exists(version):
    """检查版本是否已存在于 versions.json 中且哈希值完整"""
    data_file = "data/versions.json"
    
    if not os.path.exists(data_file):
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查这个版本是否存在
    existing_version = None
    for v in data.get('versions', []):
        if v['version'] == version:
            existing_version = v
            break
    
    if not existing_version:
        return False
    
    # 检查所有哈希值是否都存在
    for arch_files in existing_version.get('files', {}).values():
        for file_info in arch_files.values():
            if not file_info.get('sha256'):
                return False
    
    return True

def update_last_checked():
    """更新最后检查时间"""
    data_file = "data/versions.json"
    current_time = datetime.utcnow().isoformat() + "Z"
    
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "versions": [],
            "latest_version": "",
            "last_checked": ""
        }
    
    data['last_checked'] = current_time
    
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    version = get_current_version()
    
    if not version:
        print("无法获取版本号")
        update_last_checked()
        print("has_new_version=false")
        return
    
    print(f"检测到版本: {version}")
    
    # 检查是否已发布过这个版本
    last_release_file = "data/last_release_version.txt"
    if os.path.exists(last_release_file):
        with open(last_release_file, 'r', encoding='utf-8') as f:
            last_version = f.read().strip()
        
        if last_version == version:
            print(f"版本 {version} 已发布，跳过处理")
            update_last_checked()
            print("has_new_version=false")
            return
    
    # 检查版本是否已存在且哈希值完整
    if check_version_exists(version):
        print(f"版本 {version} 已存在且哈希值完整")
        update_last_checked()
        print("has_new_version=false")
        return
    
    # 发现新版本或需要更新哈希
    print("has_new_version=true")
    print(f"new_version={version}")
    
    # 保存最新版本号到临时文件，供下载步骤使用
    os.makedirs("data", exist_ok=True)
    with open("data/pending_version.txt", "w", encoding='utf-8') as f:
        f.write(version)
    
    update_last_checked()

if __name__ == "__main__":
    main()