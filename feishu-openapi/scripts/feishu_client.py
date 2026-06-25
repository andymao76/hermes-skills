#!/usr/bin/env python3
"""
飞书开放平台 API 辅助脚本。

使用前设置环境变量:
  export FEISHU_APP_ID="cli_xxxxxxxxxxx"
  export FEISHU_APP_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

用法:
  python feishu_client.py search-chat <群名关键词>
  python feishu_client.py send-text <open_id> <消息内容>
  python feishu_client.py send-image <open_id> <图片路径>
  python feishu_client.py upload-file <文件路径> <文件类型> [文件名]
  python feishu_client.py chat-members <chat_id>
"""

import json
import os
import sys

import lark_oapi as lark
from lark_oapi.api.im.v1 import *


def get_client():
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        print("错误: 请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量", file=sys.stderr)
        sys.exit(1)
    return lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.ERROR) \
        .build()


def search_chat(query: str, page_size: int = 20):
    client = get_client()
    request = SearchChatRequest.builder() \
        .user_id_type("open_id") \
        .query(query) \
        .page_size(page_size) \
        .build()
    response = client.im.v1.chat.search(request)
    if not response.success():
        print(json.dumps({"error": True, "code": response.code, "msg": response.msg}))
        sys.exit(1)
    print(lark.JSON.marshal(response.data, indent=2))


def send_text(receive_id: str, text: str, receive_id_type: str = "open_id"):
    client = get_client()
    content = json.dumps({"text": text})
    request = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type("text")
            .content(content)
            .build()) \
        .build()
    response = client.im.v1.message.create(request)
    if not response.success():
        print(json.dumps({"error": True, "code": response.code, "msg": response.msg}))
        sys.exit(1)
    print(lark.JSON.marshal(response.data, indent=2))


def send_image(receive_id: str, image_path: str, receive_id_type: str = "open_id"):
    """上传图片并发送"""
    client = get_client()

    # 上传图片
    with open(image_path, "rb") as f:
        img_req = CreateImageRequest.builder() \
            .request_body(CreateImageRequestBody.builder()
                .image_type("message")
                .image(f)
                .build()) \
            .build()
        img_resp = client.im.v1.image.create(img_req)
        if not img_resp.success():
            print(json.dumps({"error": True, "code": img_resp.code, "msg": f"上传图片失败: {img_resp.msg}"}))
            sys.exit(1)
        image_key = img_resp.data.image_key

    # 发送图片消息
    content = json.dumps({"image_key": image_key})
    msg_req = CreateMessageRequest.builder() \
        .receive_id_type(receive_id_type) \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type("image")
            .content(content)
            .build()) \
        .build()
    msg_resp = client.im.v1.message.create(msg_req)
    if not msg_resp.success():
        print(json.dumps({"error": True, "code": msg_resp.code, "msg": msg_resp.msg}))
        sys.exit(1)
    print(lark.JSON.marshal(msg_resp.data, indent=2))


def upload_file(file_path: str, file_type: str, file_name: str = None):
    client = get_client()
    if not file_name:
        file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        request = CreateFileRequest.builder() \
            .request_body(CreateFileRequestBody.builder()
                .file_type(file_type)
                .file_name(file_name)
                .file(f)
                .build()) \
            .build()
        response = client.im.v1.file.create(request)
    if not response.success():
        print(json.dumps({"error": True, "code": response.code, "msg": response.msg}))
        sys.exit(1)
    print(lark.JSON.marshal(response.data, indent=2))


def get_chat_members(chat_id: str):
    client = get_client()
    request = GetChatMembersRequest.builder() \
        .chat_id(chat_id) \
        .member_id_type("user_id") \
        .build()
    response = client.im.v1.chat_members.get(request)
    if not response.success():
        print(json.dumps({"error": True, "code": response.code, "msg": response.msg}))
        sys.exit(1)
    print(lark.JSON.marshal(response.data, indent=2))


def usage():
    print(__doc__, file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()

    cmd = sys.argv[1]

    if cmd == "search-chat":
        if len(sys.argv) < 3:
            print("用法: python feishu_client.py search-chat <群名关键词>", file=sys.stderr)
            sys.exit(1)
        search_chat(sys.argv[2])

    elif cmd == "send-text":
        if len(sys.argv) < 4:
            print("用法: python feishu_client.py send-text <open_id> <消息内容>", file=sys.stderr)
            sys.exit(1)
        send_text(sys.argv[2], sys.argv[3])

    elif cmd == "send-image":
        if len(sys.argv) < 4:
            print("用法: python feishu_client.py send-image <open_id> <图片路径>", file=sys.stderr)
            sys.exit(1)
        send_image(sys.argv[2], sys.argv[3])

    elif cmd == "upload-file":
        if len(sys.argv) < 4:
            print("用法: python feishu_client.py upload-file <文件路径> <文件类型> [文件名]", file=sys.stderr)
            sys.exit(1)
        file_name = sys.argv[4] if len(sys.argv) > 4 else None
        upload_file(sys.argv[2], sys.argv[3], file_name)

    elif cmd == "chat-members":
        if len(sys.argv) < 3:
            print("用法: python feishu_client.py chat-members <chat_id>", file=sys.stderr)
            sys.exit(1)
        get_chat_members(sys.argv[2])

    else:
        print(f"未知命令: {cmd}", file=sys.stderr)
        usage()
