#!/usr/bin/env python3
import requests
import json
import os
import hashlib
from datetime import datetime

def download_and_hash(url, filename):
    """下载文件并计算SHA256哈希值"""
    try:
        print(f"下载: {filename}")
        # 增加超时时间，因为文件可能较大
        response = requests.get(url, stream=True, timeout=60)
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

def main():
    # 读取待处理的版本
    pending_file = "data/pending_version.txt"
    if not os.path.exists(pending_file):
        print("没有待处理的版本")
        return
    
    with open(pending_file, 'r', encoding='utf-8') as f:
        version = f.read().strip()
    
    print(f"开始下载版本: {version}")
    
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
    all_success = True
    for arch, pkg_type, url in files_to_download:
        # 转换扩展名大小写
        ext_map = {
            "deb": "deb",
            "rpm": "rpm", 
            "appimage": "appimage"
        }
        filename = f"wechat_linux_{arch}_{version}.{ext_map[pkg_type]}"
        sha256, size = download_and_hash(url, filename)
        
        files_data[arch][pkg_type] = {
            "filename": filename,
            "sha256": sha256,
            "size": size,
            "url": url,
            "download_url": f"https://github.com/Aozora-Wings/wechat-linux-monitor/releases/download/v{version}/{filename}"
        }
        
        if not sha256:
            all_success = False
            print(f"警告: {filename} 下载失败")
    
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
    
    # 检查版本是否已存在，更新或添加
    existing_version_index = None
    for i, v in enumerate(data.get('versions', [])):
        if v['version'] == version:
            existing_version_index = i
            break
    
    if existing_version_index is not None:
        data['versions'][existing_version_index] = new_version_data
        print(f"更新版本 {version} 的数据")
    else:
        data['versions'] = data.get('versions', []) + [new_version_data]
        print(f"添加新版本: {version}")
    
    data['latest_version'] = version
    data['last_checked'] = current_time
    
    # 保存数据
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 清理临时文件
    os.remove(pending_file)
    
    if all_success:
        print("所有文件下载完成")
    else:
        print("部分文件下载失败，请检查")

if __name__ == "__main__":
    main()