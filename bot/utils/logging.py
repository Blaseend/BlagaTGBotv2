def debug_log(context: str, data: dict = None):
    print(f"\n⚡️ [DEBUG] {context}")
    if data:
        print(f"Данные состояния: {data}")