#!/usr/bin/env python3
"""
IMA知识库 → 本地知识库 同步脚本 (Python版)
读取IMA所有知识库内容，同步到本地 knowledge/ima-sync/
优先使用此版本而非Node.js版，避免execSync在Hermes环境下的stdout捕获问题。
"""
import json, os, subprocess, sys
from pathlib import Path

HOME = os.environ['HOME']
SKILL_DIR = os.path.join(HOME, '.hermes/skills/ima')
LOCAL_KB_DIR = os.path.join(HOME, 'knowledge/ima-sync')
SYNC_STATE_FILE = os.path.join(LOCAL_KB_DIR, '.sync_state.json')
IMA_API = os.path.join(SKILL_DIR, 'ima_api.cjs')

def call_ima(api_path, body):
    cmd = ['node', IMA_API, api_path, json.dumps(body)]
    try:
        result = subprocess.run(cmd, cwd=SKILL_DIR, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"  API调用失败: {api_path} (exit {result.returncode})")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"  API异常: {e}")
        return None

def load_state():
    if os.path.exists(SYNC_STATE_FILE):
        with open(SYNC_STATE_FILE) as f:
            return json.load(f)
    return {"synced_media_ids": [], "last_sync_at": ""}

def save_state(state):
    os.makedirs(LOCAL_KB_DIR, exist_ok=True)
    state["last_sync_at"] = __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(SYNC_STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_all_knowledge_bases():
    kbs = []
    cursor = ""
    while True:
        body = {"query": "", "limit": 20}
        if cursor:
            body["cursor"] = cursor
        resp = call_ima('openapi/wiki/v1/search_knowledge_base', body)
        if not resp or resp.get('code') != 0:
            break
        info_list = resp.get('data', {}).get('info_list', [])
        for kb in info_list:
            kbs.append({'id': kb['kb_id'], 'name': kb['kb_name'],
                        'creator': kb.get('creator', ''),
                        'role_type': kb.get('role_type', ''),
                        'base_type': kb.get('base_type', '')})
        cursor = resp.get('data', {}).get('next_cursor', '')
        if not cursor or resp.get('data', {}).get('is_end'):
            break
        if len(kbs) >= 100:
            break
    return kbs

def get_knowledge_list(kb_id):
    items = []
    cursor = ""
    while True:
        body = {"knowledge_base_id": kb_id, "limit": 50}
        if cursor:
            body["cursor"] = cursor
        resp = call_ima('openapi/wiki/v1/get_knowledge_list', body)
        if not resp or resp.get('code') != 0:
            break
        kb_list = resp.get('data', {}).get('knowledge_list', [])
        for item in kb_list:
            item['kb_id'] = kb_id
            items.append(item)
        cursor = resp.get('data', {}).get('next_cursor', '')
        if resp.get('data', {}).get('is_end'):
            break
        if not cursor:
            break
    return items

def get_media_info(media_id, kb_id):
    resp = call_ima('openapi/wiki/v1/get_media_info',
                    {"knowledge_base_id": kb_id, "media_id": media_id})
    if resp and resp.get('code') == 0:
        return resp.get('data', {})
    return None

def sanitize_filename(name):
    invalid = '<>:"/\\|?*\n\r\t'
    for c in invalid:
        name = name.replace(c, '')
    return name.strip()[:200]

def main():
    print("🔄 开始同步 IMA 知识库...")
    print(f"📁 本地目录: {LOCAL_KB_DIR}")
    os.makedirs(LOCAL_KB_DIR, exist_ok=True)
    state = load_state()
    synced = set(state.get('synced_media_ids', []))
    kbs = get_all_knowledge_bases()
    print(f"  找到 {len(kbs)} 个知识库\n")
    total_new = total_skipped = 0
    total_all = len(synced)
    for kb in kbs:
        kb_name, kb_id = kb['name'], kb['id']
        print(f"📂 知识库: {kb_name} ({kb.get('base_type', '')})")
        items = get_knowledge_list(kb_id)
        print(f"   内容数量: {len(items)}")
        kb_dir = os.path.join(LOCAL_KB_DIR, sanitize_filename(kb_name))
        os.makedirs(kb_dir, exist_ok=True)
        for item in items:
            media_id = item.get('media_id', '')
            if not media_id:
                continue
            if media_id in synced:
                total_skipped += 1
                continue
            title = item.get('title', media_id)
            safe_title = sanitize_filename(title)
            media_info = get_media_info(media_id, kb_id)
            if media_info:
                meta_path = os.path.join(kb_dir, f"{safe_title}.meta.json")
                with open(meta_path, 'w') as f:
                    json.dump(media_info, f, ensure_ascii=False, indent=2)
                url_info = media_info.get('url_info', {})
                url = url_info.get('url', '')
                if url:
                    url_path = os.path.join(kb_dir, f"{safe_title}.url.txt")
                    with open(url_path, 'w') as f:
                        f.write(url + '\n')
            synced.add(media_id)
            total_new += 1
            total_all += 1
            if total_new % 10 == 0:
                print(f"  已处理 {total_new} 个新条目...")
        print()
    state['synced_media_ids'] = list(synced)
    save_state(state)
    print("=" * 50)
    print(f"📊 同步完成!  新增: {total_new}  跳过: {total_skipped}  总计: {total_all}")
    print("=" * 50)

if __name__ == '__main__':
    main()
