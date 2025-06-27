#!/usr/bin/env python3
"""
ログインスペクターCLIツール

このツールは、app.logファイルから特定の条件でログを検索・絞り込みできます。
"""

import argparse
import re
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

class LogInspector:
    """ログファイルを検索・絞り込みするクラス"""
    
    def __init__(self, log_file: str = "app.log"):
        """
        初期化
        
        Args:
            log_file: ログファイルのパス
        """
        self.log_file = log_file
        self.log_entries = []
        
    def load_logs(self) -> bool:
        """
        ログファイルを読み込む
        
        Returns:
            bool: 読み込みが成功したかどうか
        """
        try:
            if not os.path.exists(self.log_file):
                print(f"❌ ログファイルが見つかりません: {self.log_file}")
                return False
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.log_entries = []
            current_entry = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # ログエントリの開始を検出（タイムスタンプで始まる行）
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)', line)
                if timestamp_match:
                    # 前のエントリを保存
                    if current_entry:
                        self.log_entries.append(current_entry)
                    
                    # 新しいエントリを開始
                    timestamp, level, message = timestamp_match.groups()
                    current_entry = {
                        'timestamp': timestamp,
                        'level': level,
                        'message': message,
                        'raw_line': line
                    }
                else:
                    # マルチラインログの続き
                    if current_entry:
                        current_entry['message'] += '\n' + line
                        current_entry['raw_line'] += '\n' + line
            
            # 最後のエントリを保存
            if current_entry:
                self.log_entries.append(current_entry)
            
            print(f"✅ ログファイルを読み込みました: {len(self.log_entries)} エントリ")
            return True
            
        except Exception as e:
            print(f"❌ ログファイルの読み込みに失敗しました: {str(e)}")
            return False
    
    def filter_by_structure_id(self, structure_id: str) -> List[Dict[str, Any]]:
        """
        構成IDでフィルタリング
        
        Args:
            structure_id: 構成ID
            
        Returns:
            List[Dict[str, Any]]: フィルタリングされたログエントリ
        """
        filtered = []
        for entry in self.log_entries:
            if structure_id.lower() in entry['message'].lower():
                filtered.append(entry)
        return filtered
    
    def filter_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """
        ユーザーIDでフィルタリング
        
        Args:
            user_id: ユーザーID
            
        Returns:
            List[Dict[str, Any]]: フィルタリングされたログエントリ
        """
        filtered = []
        for entry in self.log_entries:
            if user_id.lower() in entry['message'].lower():
                filtered.append(entry)
        return filtered
    
    def filter_by_level(self, level: str) -> List[Dict[str, Any]]:
        """
        ログレベルでフィルタリング
        
        Args:
            level: ログレベル（INFO, WARNING, ERROR, DEBUG）
            
        Returns:
            List[Dict[str, Any]]: フィルタリングされたログエントリ
        """
        filtered = []
        for entry in self.log_entries:
            if entry['level'].upper() == level.upper():
                filtered.append(entry)
        return filtered
    
    def filter_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        日付範囲でフィルタリング
        
        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
            
        Returns:
            List[Dict[str, Any]]: フィルタリングされたログエントリ
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            
            filtered = []
            for entry in self.log_entries:
                try:
                    entry_dt = datetime.strptime(entry['timestamp'][:10], '%Y-%m-%d')
                    if start_dt <= entry_dt < end_dt:
                        filtered.append(entry)
                except ValueError:
                    continue
            
            return filtered
        except ValueError as e:
            print(f"❌ 日付形式が正しくありません: {str(e)}")
            return []
    
    def filter_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        キーワードでフィルタリング
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            List[Dict[str, Any]]: フィルタリングされたログエントリ
        """
        filtered = []
        for entry in self.log_entries:
            if keyword.lower() in entry['message'].lower():
                filtered.append(entry)
        return filtered
    
    def display_logs(self, logs: List[Dict[str, Any]], show_timestamp: bool = True, show_level: bool = True):
        """
        ログを表示する
        
        Args:
            logs: 表示するログエントリのリスト
            show_timestamp: タイムスタンプを表示するかどうか
            show_level: ログレベルを表示するかどうか
        """
        if not logs:
            print("📭 該当するログが見つかりませんでした")
            return
        
        print(f"\n📋 検索結果: {len(logs)} 件のログエントリ")
        print("=" * 80)
        
        for i, entry in enumerate(logs, 1):
            prefix = ""
            if show_timestamp:
                prefix += f"[{entry['timestamp']}] "
            if show_level:
                prefix += f"[{entry['level']}] "
            
            # メッセージを整形
            message = entry['message']
            if len(message) > 100:
                message = message[:97] + "..."
            
            print(f"{i:3d}. {prefix}{message}")
        
        print("=" * 80)
    
    def get_statistics(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ログの統計情報を取得
        
        Args:
            logs: 対象のログエントリのリスト
            
        Returns:
            Dict[str, Any]: 統計情報
        """
        if not logs:
            return {}
        
        stats = {
            'total_entries': len(logs),
            'levels': {},
            'structure_ids': set(),
            'user_ids': set(),
            'date_range': {'start': None, 'end': None}
        }
        
        for entry in logs:
            # ログレベルの集計
            level = entry['level']
            stats['levels'][level] = stats['levels'].get(level, 0) + 1
            
            # 構成IDの抽出
            structure_match = re.search(r'structure_id: ([a-zA-Z0-9_-]+)', entry['message'])
            if structure_match:
                stats['structure_ids'].add(structure_match.group(1))
            
            # ユーザーIDの抽出
            user_match = re.search(r'ユーザー: ([a-zA-Z0-9_-]+)', entry['message'])
            if user_match:
                stats['user_ids'].add(user_match.group(1))
            
            # 日付範囲の更新
            try:
                entry_date = datetime.strptime(entry['timestamp'][:10], '%Y-%m-%d')
                if stats['date_range']['start'] is None or entry_date < stats['date_range']['start']:
                    stats['date_range']['start'] = entry_date
                if stats['date_range']['end'] is None or entry_date > stats['date_range']['end']:
                    stats['date_range']['end'] = entry_date
            except ValueError:
                continue
        
        # setをlistに変換
        stats['structure_ids'] = list(stats['structure_ids'])
        stats['user_ids'] = list(stats['user_ids'])
        
        return stats
    
    def display_statistics(self, stats: Dict[str, Any]):
        """
        統計情報を表示
        
        Args:
            stats: 統計情報
        """
        if not stats:
            return
        
        print("\n📊 統計情報")
        print("-" * 40)
        print(f"総エントリ数: {stats['total_entries']}")
        
        if stats['levels']:
            print("\nログレベル別:")
            for level, count in sorted(stats['levels'].items()):
                print(f"  {level}: {count}件")
        
        if stats['structure_ids']:
            print(f"\n関連構成ID: {', '.join(stats['structure_ids'])}")
        
        if stats['user_ids']:
            print(f"関連ユーザーID: {', '.join(stats['user_ids'])}")
        
        if stats['date_range']['start'] and stats['date_range']['end']:
            print(f"日付範囲: {stats['date_range']['start'].strftime('%Y-%m-%d')} ～ {stats['date_range']['end'].strftime('%Y-%m-%d')}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="ログファイルを検索・絞り込みするCLIツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python log_inspector.py --structure-id test-001
  python log_inspector.py --user-id user123 --level INFO
  python log_inspector.py --start-date 2025-06-19 --end-date 2025-06-20
  python log_inspector.py --keyword "構成評価"
        """
    )
    
    parser.add_argument('--log-file', default='app.log', help='ログファイルのパス (デフォルト: app.log)')
    parser.add_argument('--structure-id', help='構成IDでフィルタリング')
    parser.add_argument('--user-id', help='ユーザーIDでフィルタリング')
    parser.add_argument('--level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='ログレベルでフィルタリング')
    parser.add_argument('--start-date', help='開始日 (YYYY-MM-DD形式)')
    parser.add_argument('--end-date', help='終了日 (YYYY-MM-DD形式)')
    parser.add_argument('--keyword', help='キーワードでフィルタリング')
    parser.add_argument('--no-timestamp', action='store_true', help='タイムスタンプを非表示')
    parser.add_argument('--no-level', action='store_true', help='ログレベルを非表示')
    parser.add_argument('--stats', action='store_true', help='統計情報を表示')
    parser.add_argument('--raw', action='store_true', help='生のログ行を表示')
    
    args = parser.parse_args()
    
    # ログインスペクターを初期化
    inspector = LogInspector(args.log_file)
    
    # ログファイルを読み込み
    if not inspector.load_logs():
        sys.exit(1)
    
    # フィルタリング
    filtered_logs = inspector.log_entries
    
    if args.structure_id:
        filtered_logs = inspector.filter_by_structure_id(args.structure_id)
        print(f"🔍 構成ID '{args.structure_id}' でフィルタリング: {len(filtered_logs)}件")
    
    if args.user_id:
        filtered_logs = inspector.filter_by_user_id(args.user_id)
        print(f"🔍 ユーザーID '{args.user_id}' でフィルタリング: {len(filtered_logs)}件")
    
    if args.level:
        filtered_logs = inspector.filter_by_level(args.level)
        print(f"🔍 ログレベル '{args.level}' でフィルタリング: {len(filtered_logs)}件")
    
    if args.start_date and args.end_date:
        filtered_logs = inspector.filter_by_date_range(args.start_date, args.end_date)
        print(f"🔍 日付範囲 '{args.start_date}' ～ '{args.end_date}' でフィルタリング: {len(filtered_logs)}件")
    
    if args.keyword:
        filtered_logs = inspector.filter_by_keyword(args.keyword)
        print(f"🔍 キーワード '{args.keyword}' でフィルタリング: {len(filtered_logs)}件")
    
    # 結果を表示
    if args.raw:
        for entry in filtered_logs:
            print(entry['raw_line'])
    else:
        inspector.display_logs(
            filtered_logs,
            show_timestamp=not args.no_timestamp,
            show_level=not args.no_level
        )
    
    # 統計情報を表示
    if args.stats:
        stats = inspector.get_statistics(filtered_logs)
        inspector.display_statistics(stats)


if __name__ == "__main__":
    main() 