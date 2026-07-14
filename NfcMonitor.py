#!/usr/bin/env python3
# This program watches a USB serial connection for messages from a custom NFC tag reader.
# The reader sends plain text lines in one of two formats:
#   TAG_FOUND, <timestamp>, <tag_id>   -> a card was detected
#   NO_TAG, <timestamp>                -> no card is present
#
# We don't know in advance which port the reader is plugged into, so we scan
# all available ports and test each one until we find it.


# このプログラムは、USBシリアル接続を監視し、独自のNFCタグリーダーからのメッセージを受信します。
# リーダーは、以下の2種類のテキスト形式でメッセージを送信します。
#   TAG_FOUND, <timestamp>, <tag_id>   -> カードを検出した場合
#   NO_TAG, <timestamp>                -> カードがない場合
# リーダーがどのポートに接続されているか事前にはわからないため、
# 利用可能なすべてのポートを順に調べてリーダーを探します。

import time
import serial
import serial.tools.list_ports

BAUD_RATE = 115200  # Must match the reader's transmission speed / リーダーの送信速度と一致させる必要がある
READ_TIMEOUT = 1  # Max seconds to wait for a line before giving up / 1行を待つ最大時間（秒）


def find_reader_port():
    # Try each serial port in turn: open it briefly and check whether the
    # incoming text looks like a message from our reader.
    # 各シリアルポートを順番に試し、一時的に開いて受信データが
    # 目的のリーダーからのメッセージかどうかを確認する。
    for port in serial.tools.list_ports.comports():
        try:
            with serial.Serial(port.device, BAUD_RATE, timeout=READ_TIMEOUT) as ser:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("TAG_FOUND") or line.startswith("NO_TAG"):
                    return port.device
        except (OSError, serial.SerialException):
            # This port didn't work (e.g. busy or not our device) -- skip it.
            # このポートは使用できなかった（使用中や対象外など）ためスキップする。
            continue
    return None


def parse_message(line):
    # Split the message on commas and print a human-readable result.
    # メッセージをカンマで分割し、人が読みやすい形式で表示する。
    parts = [p.strip() for p in line.split(",")]
    if parts[0] == "TAG_FOUND" and len(parts) == 3:
        _, timestamp, tag_id = parts
        print(f"Tag found: {tag_id} at {timestamp}")
    elif parts[0] == "NO_TAG" and len(parts) == 2:
        _, timestamp = parts
        print(f"No tag at {timestamp}")
    else:
        print(f"Unrecognized message: {line}")


def monitor(port_name):
    # Keep reading lines from the reader for as long as the connection stays open.
    # 接続が続く限り、リーダーからのメッセージを読み取り続ける。
    print(f"Connected to NFC reader on {port_name}")
    with serial.Serial(port_name, BAUD_RATE, timeout=READ_TIMEOUT) as ser:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                parse_message(line)


def main():
    # Keep trying to find and connect to the reader, and automatically
    # reconnect if the connection is ever lost (e.g. the cable is unplugged).
    # リーダーが見つかるまで探し続け、接続が切れた場合（ケーブルが
    # 抜けた場合など）は自動的に再接続する。
    while True:
        port_name = find_reader_port()
        if port_name is None:
            print("NFC reader not found, retrying...")
            time.sleep(2)
            continue
        try:
            monitor(port_name)
        except (OSError, serial.SerialException):
            print("Lost connection to NFC reader, reconnecting...")
            time.sleep(2)


if __name__ == "__main__":
    # Run the program, and exit quietly on Ctrl+C.
    # プログラムを実行し、Ctrl+Cが押されたら静かに終了する。
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
