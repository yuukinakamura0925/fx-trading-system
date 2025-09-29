#!/usr/bin/env python3
"""
環境変数設定のテストスクリプト
.envファイルからAPIキーが正しく読み込まれているか確認
"""

import os
import sys

def test_env_variables():
    """環境変数の読み込みテスト"""

    print("=" * 60)
    print("🔧 環境変数テスト")
    print("=" * 60)

    # 基本的な環境変数
    env_vars = {
        'OPENAI_API_KEY': 'OpenAI APIキー',
        'DJANGO_SECRET_KEY': 'Django秘密鍵',
        'DJANGO_DEBUG': 'Djangoデバッグモード',
        'POSTGRES_DB': 'PostgreSQLデータベース名',
        'POSTGRES_USER': 'PostgreSQLユーザー',
        'LLM_MODEL': 'LLMモデル名',
        'LLM_TEMPERATURE': 'LLM温度設定',
    }

    print("\n📋 環境変数の読み込み状態:")
    print("-" * 40)

    for key, description in env_vars.items():
        value = os.getenv(key, '未設定')

        # APIキーは部分的に隠す
        if 'KEY' in key and value != '未設定':
            if len(value) > 10:
                display_value = f"{value[:8]}...{value[-4:]}"
            else:
                display_value = "***設定済み***"
        else:
            display_value = value

        status = "✅" if value != '未設定' else "❌"
        print(f"{status} {description:20} : {display_value}")

    # Django設定の読み込みテスト
    print("\n📋 Django設定の読み込みテスト:")
    print("-" * 40)

    try:
        # Django設定を読み込む
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fx_trading.settings')
        import django
        django.setup()

        from django.conf import settings

        print(f"✅ Django設定読み込み成功")
        print(f"   - DEBUG: {settings.DEBUG}")
        print(f"   - ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

        # OpenAI APIキーの確認
        if hasattr(settings, 'OPENAI_API_KEY'):
            api_key = settings.OPENAI_API_KEY
            if api_key:
                print(f"✅ OpenAI APIキー: 設定済み ({api_key[:8]}...)")
            else:
                print(f"⚠️ OpenAI APIキー: 空文字列")
        else:
            print(f"❌ OpenAI APIキー: 設定なし")

        # LLM設定の確認
        if hasattr(settings, 'LLM_CONFIG'):
            llm_config = settings.LLM_CONFIG
            print(f"✅ LLM設定:")
            print(f"   - モデル: {llm_config.get('model', '未設定')}")
            print(f"   - 温度: {llm_config.get('temperature', '未設定')}")
            print(f"   - 最大トークン: {llm_config.get('max_tokens', '未設定')}")

    except Exception as e:
        print(f"❌ Django設定読み込みエラー: {e}")

    # ハイブリッドアナライザーのテスト
    print("\n📋 ハイブリッドアナライザーのテスト:")
    print("-" * 40)

    try:
        from analysis.hybrid_analyzer import HybridFXAnalyzer

        analyzer = HybridFXAnalyzer()

        # LLMアナライザーのAPIキー確認
        if analyzer.llm_analyzer.api_key:
            print(f"✅ LLMアナライザー: APIキー設定済み")
            print(f"   キーの長さ: {len(analyzer.llm_analyzer.api_key)}文字")
        else:
            print(f"⚠️ LLMアナライザー: APIキーなし（アルゴリズム分析のみ）")

    except Exception as e:
        print(f"❌ アナライザー初期化エラー: {e}")

    print("\n" + "=" * 60)

    # 環境変数設定のアドバイス
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key or api_key == 'your-actual-openai-api-key-here':
        print("\n💡 OpenAI APIキーを設定するには:")
        print("   1. .envファイルを開く")
        print("   2. OPENAI_API_KEY=sk-... の行を編集")
        print("   3. docker-compose restart で再起動")
        print("\n   APIキーの取得: https://platform.openai.com/api-keys")
    else:
        print("\n✅ 環境変数の設定が完了しています！")


if __name__ == "__main__":
    test_env_variables()