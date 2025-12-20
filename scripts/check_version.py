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

def save_version_data(version):
    """保存版本数据"""
    data_file = "data/versions.json"
    
    # 加载现有数据
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {'versions': []}
    
    # 检查版本是否已存在
    version_exists = any(v['version'] == version for v in data['versions'])
    
    if not version_exists:
        # 添加新版本
        new_version_data = {
            'version': version,
            'timestamp': datetime.utcnow().isoformat(),
            'architectures': {
                'x86': ['deb', 'rpm', 'AppImage'],
                'arm64': ['deb', 'rpm', 'AppImage'],
                'loongarch': ['deb']
            }
        }
        
        data['versions'].append(new_version_data)
        data['last_checked'] = datetime.utcnow().isoformat()
        data['latest_version'] = version
        
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
    
    # 保存版本数据
    save_version_data(version)

if __name__ == "__main__":
    main()