import time
import json
import random
import requests

import images

# Get your user ID by sniffing the network traffic
USER_ID = "000000000000000000000000"
# Coordinates of the top-left corner of the image
START_X = 0
START_Y = 0

URL = "https://wappupixel.paitsiossa.net/api/board"
AUTH_URL = "https://wappupixel.paitsiossa.net/api/auth/token"
SLEEP_INTERVAL = 60.1  # Time in seconds
CHECK_MODE = "sequential"  # Can be 'sequential' or 'random'

color_list = [
    4294771198,
    4292736511,
    4280953765,
    4286064930,
    4294943741,
    4282754815,
    4278190080,
    4288021345,
    4284779614,
    4279123559,
    4281546970,
    4283755506,
    4294836224,
    4286611584,
    4280498180,
    4294639613
]

headers = {
    'accept': '*/*',
    'accept-language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://wappupixel.paitsiossa.net',
    'referer': 'https://wappupixel.paitsiossa.net/',
    'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}


def fetch_board():
    print("Fetching board data...")
    response = requests.get(URL)
    response.raise_for_status()
    print("Board data fetched.")
    return response.json()


def fetch_validation_cookie():
    data = json.dumps({"userId": USER_ID})
    response = requests.post(AUTH_URL, data=data, headers=headers)
    response.raise_for_status()
    cookie_value = response.cookies.get('validation')
    return {'validation': cookie_value}


def send_pixel_correction(x, y, correct_index):
    payload = {
        "pixels": [{"x": x, "y": y, "color": correct_index}],
        "userId": USER_ID,
        "adminMode": False
    }
    cookies = fetch_validation_cookie()
    response = requests.post(URL, data=json.dumps(
        payload), cookies=cookies, headers=headers)
    try:
        response.raise_for_status()
        print("Corrected pixel at (", x, ",", y, ") to color index", correct_index)
    except requests.exceptions.HTTPError as err:
        print("HTTP error occurred:", err)
        print("Response status code:", response.status_code)
        print("Response text:", response.text)


def forbidden(x, y):
    if x >= 100 and x <= 115 and y >= 42 and y <= 68:
        return True
    return False


def check_pixels(board, grid_size, start_x, start_y, width, height, target_indices, mode):
    if mode == "sequential":
        for y in range(height):
            for x in range(width):
                index_x = start_x + x
                index_y = start_y + y
                board_color = board[index_y * grid_size + index_x]
                expected_index = target_indices[y][x]
                if expected_index != 99 and board_color != color_list[expected_index] and not forbidden(index_x, index_y):
                    send_pixel_correction(index_x, index_y, expected_index)
                    return False
        return True
    elif mode == "random":
        checked_positions = set()
        attempts = 0
        max_attempts = len(target_indices) * len(target_indices[0])
        while attempts < max_attempts:
            x = random.randint(start_x, start_x + width - 1)
            y = random.randint(start_y, start_y + height - 1)
            if (x, y) not in checked_positions:
                checked_positions.add((x, y))
                board_color = board[y * grid_size + x]
                expected_index = target_indices[(y - start_y) % height][(x - start_x) % width]
                if expected_index != 99 and board_color != color_list[expected_index] and not forbidden(x, y):
                    send_pixel_correction(x, y, expected_index)
                    return False
            attempts += 1


def main():
    target_indices = images.moikkuli

    width = len(target_indices[0])
    height = len(target_indices)

    while True:
        board_data = fetch_board()
        board = board_data['board']
        grid_size = board_data['gridSize']
        if check_pixels(board, grid_size, START_X, START_Y, width, height, target_indices, mode=CHECK_MODE):
            print("All pixels are correct.")

        print("Sleeping for", SLEEP_INTERVAL, "seconds...")
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main()
