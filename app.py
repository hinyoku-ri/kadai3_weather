import flet as ft
import requests
from db import init_db, get_conn
from datetime import datetime
import json

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"


def fetch_areas():
    data = requests.get(AREA_URL, timeout=10).json()
    offices = data["offices"] 

    areas = []
    for code, info in offices.items():
        areas.append((code, info["name"]))

    areas.sort(key=lambda x: x[1])
    return areas


def fetch_forecast(code: str):
    url = FORECAST_URL.format(code=code)
    return requests.get(url, timeout=10).json()

def load_latest_forecast_from_db(code: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM forecast_runs
        WHERE area_code = ?
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (code,)
    )
    row = cur.fetchone()
    if row is None:
        conn.close()
        return []

    run_id = row["id"]

    cur.execute(
        """
        SELECT date, weather_text
        FROM forecast_items
        WHERE run_id = ?
        ORDER BY date
        """,
        (run_id,)
    )
    items = cur.fetchall()

    conn.close()
    return items


def save_forecast_to_db(code: str, data):
    fetched_at = datetime.now().isoformat(timespec="seconds")
    raw_json = json.dumps(data, ensure_ascii=False)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO areas(area_code, name) VALUES(?, ?)",
        (code, code)
    )

    cur.execute(
        "INSERT INTO forecast_runs(area_code, fetched_at, raw_json) VALUES(?, ?, ?)",
        (code, fetched_at, raw_json)
    )
    run_id = cur.lastrowid

    ts0 = data[0]["timeSeries"][0]
    time_def = ts0["timeDefines"]
    area0 = ts0["areas"][0]
    weathers = area0.get("weathers", [])

    n = min(3, len(weathers), len(time_def))
    for i in range(n):
        date = time_def[i][:10]
        cur.execute(
            "INSERT OR IGNORE INTO forecast_items(run_id, date, weather_text) VALUES(?, ?, ?)",
            (run_id, date, weathers[i])
        )

    conn.commit()
    conn.close()


def main(page: ft.Page):
    init_db()
    page.title = "天気予報アプリ"
    page.window_width = 900
    page.window_height = 600

    status = ft.Text("地域リストを取得中...")

    result_title = ft.Text("結果", size=18, weight=ft.FontWeight.BOLD)
    result_text = ft.Text("ここに結果が表示されます。")
    right_area = ft.Column([result_title, result_text], spacing=10, expand=True)

    try:
        areas = fetch_areas()
        status.value = "地域を選んで「表示」を押してください。"
    except Exception as e:
        areas = []
        status.value = f"地域リストの取得に失敗しました: {e}"

    area_dd = ft.Dropdown(
        label="地域を選択",
        width=280,
        options=[
            ft.dropdown.Option(code, f"{name}（{code}）")
            for code, name in areas
        ] if areas else [],
        value=areas[0][0] if areas else None,
    )

    def show_forecast(e):
        code = area_dd.value
        if not code:
            result_text.value = "地域を選んでください。"
            page.update()
            return

        result_text.value = "天気情報を取得中..."
        page.update()

        try:
            data = fetch_forecast(code)

            save_forecast_to_db(code, data)

            items = load_latest_forecast_from_db(code)

            lines = [f"地域コード：{code}", ""]
            for row in items:
                lines.append(row["date"])
                lines.append(row["weather_text"])
                lines.append("")

            result_text.value = "\n".join(lines).strip()

        except Exception as ex:
            result_text.value = f"天気情報の取得に失敗しました: {ex}"

        page.update()

    left = ft.Column(
        [
            ft.Text("地域選択", size=22, weight=ft.FontWeight.BOLD),
            area_dd,
            ft.ElevatedButton("表示", on_click=show_forecast),
            status,
        ],
        width=320,
    )

    page.add(
        ft.Row(
            [
                left,
                ft.VerticalDivider(),
                ft.Container(right_area, expand=True, padding=20),
            ],
            expand=True,
        )
    )


ft.app(target=main)