import re
import argparse
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
    image = cv2.imread(image)
    if image is None:
        raise Exception(f"OpenCV can't read {image}")
    cropped = image[100:138, 1375:1670]
    if debug:
        cv2.imwrite("1 cropped.png", cropped)

    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    lower_color = (15, 30, 30)
    upper_color = (30, 170, 170)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    if debug:
        cv2.imwrite("2 mask.png", mask)
    filtered = cv2.bitwise_and(cropped, cropped, mask=mask)
    if debug:
        cv2.imwrite("3 filtered.png", filtered)

    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    if debug:
        cv2.imwrite("4 gray.png", gray)
    _, thres = cv2.threshold(gray, 65, 255, cv2.THRESH_BINARY_INV)
    if debug:
        cv2.imwrite("5 thres.png", thres)

    ocr_text = pytesseract.image_to_string(thres, config='-l eng --oem 1 --psm 7')
    if debug:
        print(f"raw Tesseract text: {ocr_text}")
    ocr_text = get_qp_from_text(ocr_text)
    print(ocr_text)
    return ocr_text


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--image", required=True, help="Input image")
    arg_parser.add_argument("-d", "--debug", action='store_true', help="Write debug images")
    args = arg_parser.parse_args()
    parse_screenshot(args.image, args.debug)
