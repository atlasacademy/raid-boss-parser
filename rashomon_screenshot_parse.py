# import re
import argparse
import os
from datetime import datetime, timedelta
import numpy as np
import cv2
import pytesseract

OUTPUT_FILE = "parsed_hp.csv"

# atlasacademy/capy-drop-parser/fgo_mat_counter.py
def get_numbers_from_text(text):
    number = [s for s in text if s.isdigit()]
    return "".join(number)


def parse_screenshot(image, debug=False):
    image = cv2.imread(image)
    # image = np.asarray(image, dtype=np.uint8)
    # image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise Exception(f"OpenCV can't read {image}")
    h, w, _ = image.shape
    if w == 770 and h == 157:
        cropped = image[37:72, 342:674]
    elif w == 2160 and h == 1440:
        cropped = image[132:169, 1400:1732]
    if debug:
        cv2.imwrite("1 cropped.png", cropped)

    # hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    # It's easier to filter out white with BGR
    lower_color = np.array([163, 163, 163])
    upper_color = np.array([255, 255, 255])
    mask = cv2.inRange(cropped, lower_color, upper_color)
    # if debug:
    #     cv2.imwrite("2 mask.png", mask)
    # filtered = cv2.bitwise_and(cropped, cropped, mask=mask)
    # if debug:
    #     cv2.imwrite("3 filtered.png", filtered)

    # gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    # if debug:
    #     cv2.imwrite("4 gray.png", gray)
    # _, thres = cv2.threshold(gray, 65, 255, cv2.THRESH_BINARY_INV)
    thres = cv2.bitwise_not(mask)
    if debug:
        cv2.imwrite("5 thres.png", thres)

    ocr_text = pytesseract.image_to_string(thres, config='-l eng --oem 1 --psm 7')
    if debug:
        print(f"raw Tesseract text: {ocr_text}")
    ocr_text = get_numbers_from_text(ocr_text)
    return ocr_text


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--image", required=True, help="Input image")
    arg_parser.add_argument("-d", "--debug", action='store_true', help="Write debug images")
    arg_parser.add_argument("-a", "--append", action='store_true', help="Append output file")
    args = arg_parser.parse_args()
    result = parse_screenshot(args.image, args.debug)
    if args.append:
        created_time = os.path.basename(args.image).split(".")[0]
        created_time = datetime.utcfromtimestamp(int(created_time)) + timedelta(hours=-7)
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"{created_time}, {result}, {args.image}\n")
    print(result)
