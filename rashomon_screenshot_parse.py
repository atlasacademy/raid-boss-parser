import re
import argparse
import numpy as np
import cv2
import pytesseract


# atlasacademy/capy-drop-parser/fgo_mat_counter.py
def get_qp_from_text(text):
    qp = 0
    power = 1
    # re matches left to right so reverse the list to process lower orders of magnitude first.
    for match in re.findall('[0-9]+', text)[::-1]:
        qp += int(match) * power
        power *= 1000

    return qp


def parse_screenshot(image, debug=False):
    # image = cv2.imread(image)
    image = np.asarray(image, dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise Exception(f"OpenCV can't read {image}")
    # h, w, _ = image.shape
    # if w == 1920 and h == 1080:
    #     cropped = image[3:36, 1243:1527]
    # else:
    cropped = image[100:138, 1375:1670]
    if debug:
        cv2.imwrite("1 cropped.png", cropped)

    # hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    # It's easier to filter out white with BGR
    lower_color = (165, 165, 165)
    upper_color = (255, 255, 255)
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
    ocr_text = get_qp_from_text(ocr_text)
    return ocr_text


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--image", required=True, help="Input image")
    arg_parser.add_argument("-d", "--debug", action='store_true', help="Write debug images")
    args = arg_parser.parse_args()
    result = parse_screenshot(args.image, args.debug)
    print(result)
