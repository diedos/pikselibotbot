import time
import datetime
import statistics
import json
import random
import struct
import requests
from wasmer import engine, Store, Module, Instance
from wasmer_compiler_cranelift import Compiler

import images

# Get your user ID by sniffing the network traffic
USER_ID = "000000000000000000000000"
# Coordinates of the top-left corner of the image
START_X = 0
START_Y = 0

URL = "https://wappupixel.paitsiossa.net/api/board"
AUTH_URL = "https://wappupixel.paitsiossa.net/api/auth/token"
CHECK_MODE = "sequential"  # Can be 'sequential' or 'random'

LONG_SLEEP = lambda: random.uniform(120.0, 900.0)

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


def generate_token(color):
    t = f'{USER_ID}0{color}'  # A new UUID if dynamic, or a constant if the same always used
    e = int(time.time()) // 10 # timestamp for token generation 
    s = encode_string(t, instance.exports.__wbindgen_export_0, instance.exports.__wbindgen_export_1)
    o = instance.exports.__wbindgen_add_to_stack_pointer(-16)
    try:
        instance.exports.create_token(o, s, 26, e)
        x = read_memory(instance, o)
        #dump_memory(instance, f'{e}.txt')
        return decode_string(instance, x, 64)  # Final token processing
    finally:
        instance.exports.__wbindgen_add_to_stack_pointer(16)


def dump_memory(instance, dump_file_path):
    memory = instance.exports.memory
    memory_view = memory.uint8_view()

    memory_bytes = bytes(memory_view[:])

    with open(dump_file_path, 'wb') as dump_file:
        dump_file.write(memory_bytes)

    print(f"Memory dumped to {dump_file_path}")


def encode_string(t, allocate_func, reallocate_func=None):
    encoded_bytes = t.encode('utf-8')
    if reallocate_func is None:
        pointer = allocate_func(len(encoded_bytes), 1)
        memory_view = instance.exports.memory.uint8_view(offset=pointer)
        memory_view[0:len(encoded_bytes)] = encoded_bytes
        return pointer
    else:
        # Reallocation logic is needed
        pointer = allocate_func(len(encoded_bytes), 1)
        memory_view = instance.exports.memory.uint8_view(offset=pointer)

        for index, byte in enumerate(encoded_bytes):
            if byte > 127:
                # Handle potential reallocation for multibyte characters
                new_length = len(encoded_bytes) - index
                pointer = reallocate_func(pointer, len(encoded_bytes), new_length, 1)
                memory_view = instance.exports.memory.uint8_view(offset=pointer)
                memory_view[index:index + new_length] = encoded_bytes[index:]
                break
            else:
                memory_view[index] = byte
        return pointer


def decode_string(instance, offset, length):
    memory_view = instance.exports.memory.uint8_view()
    byte_array = memory_view[offset:offset + length]
    bytes_obj = bytes(byte_array)
    decoded_string = bytes_obj.decode('utf-8')

    return decoded_string


def read_memory(instance, offset):
    memory_view = instance.exports.memory.uint8_view()
    byte_list = memory_view[offset:offset + 4]
    bytes_obj = bytes(byte_list)
    (i,) = struct.unpack('<i', bytes_obj)
    return i


def forbidden(x, y):
    if x >= 100 and x <= 115 and y >= 42 and y <= 68:
        return True
    return False


def send_pixel_correction(x, y, correct_index):
    o = 1048560
    s = 1114120
    u = 24
    e = int(time.time()) // 10
    payload = {
        "pixels": [{"x": x, "y": y, "color": correct_index}],
        "userId": USER_ID,
        "adminMode": False,
        "validationToken": generate_token(correct_index)
    }
    response = requests.post(URL, data=json.dumps(
        payload), headers=headers)
    try:
        response.raise_for_status()
        print("Corrected pixel at (", x, ",", y, ") to color index", correct_index)
    except requests.exceptions.HTTPError as err:
        print(o, s, u, e, payload['validationToken'])
        print(json.dumps(payload))
        print("HTTP error occurred:", err)
        print("Response status code:", response.status_code)
        print("Response text:", response.text)


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


def load_precompiled_wasm_module(file_path):
    store = Store(engine.JIT(Compiler))

    with open(file_path, 'rb') as precompiled_file:
        precompiled_bytes = precompiled_file.read()
        module = Module(store, precompiled_bytes)

    instance = Instance(module)
    return instance


instance = load_precompiled_wasm_module('token.wasm')
create_token = instance.exports.create_token

night = False


def main():
    target_indices = images.moikkuli

    width = len(target_indices[0])
    height = len(target_indices)

    intervals = set()

    while True:
        night_check()

        if not night:
            random_break()
            board_data = fetch_board()
            board = board_data['board']
            grid_size = board_data['gridSize']
            if check_pixels(board, grid_size, START_X, START_Y, width, height, target_indices, mode=CHECK_MODE):
                print("All pixels are correct.")

            #sleep_interval = random.choices([random.uniform(61, 66), random.uniform(67, 80)], weights=[0.6, random.uniform(0.3, 0.6)])[0]
            sleep_interval = rng()
            print("Sleeping for", sleep_interval, "seconds...")
            intervals.add(sleep_interval)
            if len(intervals) >= 2:
                print(f'Standard deviation: {statistics.stdev(intervals)}')
            time.sleep(sleep_interval)


def rng():
    while True:
        mean = 69
        std_dev = random.uniform(5, 20)
        result = random.gauss(mean, std_dev)
        if result > 61:
            return result


def night_check():
    now = datetime.datetime.now()
    start_time = datetime.time(0, 30)
    end_time = datetime.time(5, 00)
    if (now.time() >= start_time and now.time() <= end_time):
        sleep_for = LONG_SLEEP()
        print(f'Night time. Sleeping for {sleep_for} seconds, then trying again.')
        night = True
        time.sleep(sleep_for)
    else:
        night = False


def random_break():
    execution_probability = 1 / 100
    if random.random() < execution_probability:
            sleep_for = LONG_SLEEP()
            print(f'Coffee break! Sleeping for {sleep_for} seconds.')
            time.sleep(sleep_for)


if __name__ == "__main__":
    main()

