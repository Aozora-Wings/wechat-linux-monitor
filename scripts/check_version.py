#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
import hashlib
import urllib.parse

class WeChatVersionMonitor:
    def __init__(self):
        self.url = "https://linux.weixin.qq.com"
        self.data_file = "data/versions.json"
        self.architectures = {
            "x86": {
                "deb": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.deb",
                "rpm": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.rpm",
                "appimage": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.AppImage"
            },
            "arm64": {
                "deb": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.deb",
                "rpm": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.rpm",
                "appimage": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.AppImage"
            },
            "loongarch": {
                "deb": "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_LoongArch.deb"
            }
        }
    
    def get_current_version(self):
        """获取当前页面显示的版本号"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找版本号 - 根据你提供的选择器
            version_element = soup.select_one('#__nuxt > div > div > div.main-section__bd > div.main-section__bd-version')
            
            if version_element:
                version_text = version_element.text.strip()
                # 提取版本号（例如：4.1.0）
                match = re.search(r'(\d+\.\d+\.\d+)', version_text)
                if match:
                    return match.group(1)
            
            # 备用方案：查找包含版本号的任何元素
            for element in soup.find_all(text=re.compile(r'\d+\.\d+\.\d+')):
                match = re.search(r'(\d+\.\d+\.\d+)', element)
                if match:
                    return match.group(1)
                    
            return None
            
        except Exception as e:
            print(f"获取版本失败: {e}")
            return None
    
    def download_and_hash(self, url):
        """下载文件并计算哈希值"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 计算SHA256哈希
            sha256_hash = hashlib.sha256()
            
            for chunk in response.iter_content(chunk_size=8192):
                sha256_hash.update(chunk)
            
            # 获取文件大小
            file_size = int(response.headers.get('content-length', 0))
            
            return {
                'sha256': sha256_hash.hexdigest(),
                'size': file_size,
                'url': url
            }
        except Exception as e:
            print(f"下载文件失败 {url}: {e}")
            return None
    
    def check_all_files(self, version):
        """检查所有架构的文件"""
        results = {
            'version': version,
            'timestamp': datetime.utcnow().isoformat(),
            'architectures': {}
        }
        
        for arch, packages in self.architectures.items():
            results['architectures'][arch] = {}
            
            for package_type, url in packages.items():
                print(f"检查 {arch} {package_type}...")
                file_info = self.download_and_hash(url)
                
                if file_info:
                    # 生成标准化文件名
                    filename = f"wechat_linux_{arch}_{version}_{package_type}"
                    if package_type == 'deb':
                        filename += '.deb'
                    elif package_type == 'rpm':
                        filename += '.rpm'
                    elif package_type == 'appimage':
                        filename += '.AppImage'
                    
                    results['architectures'][arch][package_type] = {
                        'filename': filename,
                        'original_url': url,
                        'hash': file_info['sha256'],
                        'size': file_info['size'],
                        'download_url': f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'user/repo')}/releases/download/v{version}/{urllib.parse.quote(filename)}"
                    }
        
        return results
    
    def load_previous_data(self):
        """加载之前的数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'versions': []}
    
    def save_data(self, data):
        """保存数据"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        existing_data = self.load_previous_data()
        
        # 检查是否已存在该版本
        version_exists = any(v['version'] == data['version'] for v in existing_data['versions'])
        
        if not version_exists:
            existing_data['versions'].append(data)
            existing_data['last_checked'] = datetime.utcnow().isoformat()
            existing_data['latest_version'] = data['version']
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"新版本发现: {data['version']}")
            return True  # 表示有新版本
        
        print(f"版本 {data['version']} 已存在")
        return False  # 表示没有新版本
    
    def generate_release_notes(self, version_data):
        """生成发布说明"""
        notes = f"# WeChat Linux {version_data['version']}\n\n"
        notes += f"自动发布于 {version_data['timestamp']}\n\n"
        
        for arch, packages in version_data['architectures'].items():
            notes += f"## {arch.upper()} 架构\n\n"
            
            for package_type, info in packages.items():
                notes += f"### {package_type.upper()}\n"
                notes += f"- **文件**: {info['filename']}\n"
                notes += f"- **大小**: {info['size']:,} 字节\n"
                notes += f"- **SHA256**: `{info['hash']}`\n"
                notes += f"- **原始URL**: {info['original_url']}\n\n"
        
        return notes

def main():
    monitor = WeChatVersionMonitor()
    
    # 获取当前版本
    current_version = monitor.get_current_version()
    
    if not current_version:
        print("无法获取版本号")
        return
    
    print(f"检测到版本: {current_version}")
    
    # 检查所有文件
    version_data = monitor.check_all_files(current_version)
    
    # 保存数据并检查是否有新版本
    is_new_version = monitor.save_data(version_data)
    
    if is_new_version:
        print("发现新版本！")
        # 设置GitHub Actions输出
        with open(os.getenv('GITHUB_OUTPUT', ''), 'a') as f:
            f.write(f"new_version=true\n")
            f.write(f"version={current_version}\n")
            f.write(f"release_notes<<EOF\n{monitor.generate_release_notes(version_data)}\nEOF\n")
    else:
        print("没有新版本")
        with open(os.getenv('GITHUB_OUTPUT', ''), 'a') as f:
            f.write(f"new_version=false\n")

if __name__ == "__main__":
    main()