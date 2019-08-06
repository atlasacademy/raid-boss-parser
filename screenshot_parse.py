import time
import argparse
import os
import pprint
import cv2
import numpy as np
import pytesseract

# from scipy import stats

OUTPUT_FILE = "parsed_hp.csv"
APOC_BOSS_TEMPLATES_FOLDER = "templates/cn-apocrypha/bosses"
SUMMER_RACE_TEAMS_TEMPLATE = "templates/na-summer-race"


def get_numbers_from_text(text):
    digits = [s for s in text if s.isdigit()]
    return "".join(digits)


def parse_hp(image, debug=False, channel_sameness_check=True):
    if debug:
        cv2.imwrite("1 cropped.png", image)

    # image = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
    sensitivity = 150
    lower_color = (255 - sensitivity, 255 - sensitivity, 255 - sensitivity)
    upper_color = (255, 255, 255)
    thres = cv2.inRange(image, lower_color, upper_color)
    thres = cv2.bitwise_not(thres)
    if debug:
        cv2.imwrite("2 thres.png", thres)
    percent_black = np.sum(thres == 0) / thres.size
    if debug:
        print(f"Percent black: {percent_black:.5f}")
    if percent_black > 0.2 and channel_sameness_check:
        colors = {i: image[:, :, i] for i in range(3)}
        channel_sameness = 10
        max_addition = 255 - channel_sameness
        for color_x, img_color in colors.items():
            # Without the maximum and minium, the addition and subtraction wraps around 0 and 255
            lower_x = np.maximum(img_color, channel_sameness) - channel_sameness
            upper_x = np.minimum(img_color, max_addition) + channel_sameness
            color_y, color_z = [c for c in colors if c != color_x]
            # If other channels y, z are not within +-sameness of x, the pixel get set to white
            # Other light colors have different varying B, G, R values while FGO whites are pretty close
            idx = (
                (colors[color_y] < lower_x)
                | (colors[color_y] > upper_x)
                | (colors[color_z] < lower_x)
                | (colors[color_z] > upper_x)
            )
            thres[idx] = 255
        if debug:
            cv2.imwrite("3 thres same rgb values.png", thres)

    #     _, labels = cv2.connectedComponents(thres, connectivity=4)
    #     most_common_component = stats.mode(np.concatenate(labels))[0][0]
    #     thres[labels == most_common_component] = 0

    ocr_text = pytesseract.image_to_string(thres, config="-l eng --oem 1 --psm 7")
    if debug:
        print(f"raw Tesseract text: {ocr_text}")
    ocr_text = get_numbers_from_text(ocr_text)
    return ocr_text


def parse_apoc_boss(image, debug=False):
    image = image[:, :104]
    bosses_list = os.listdir(APOC_BOSS_TEMPLATES_FOLDER)
    bosses_list = [b for b in bosses_list if b.endswith(".png")]
    bosses = {}
    for boss_file in bosses_list:
        boss_img = cv2.imread(os.path.join(APOC_BOSS_TEMPLATES_FOLDER, boss_file))
        if boss_img is None:
            raise Exception(f"OpenCV can't read {boss_file}")
        bosses[boss_file.split(".")[0]] = boss_img
    chosen_value = 0
    chosen_boss = ""
    for b in bosses:
        res = cv2.matchTemplate(image, bosses[b], cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if debug:
            print(f"Boss: {b}, Matching value: {max_val}")
        if max_val > chosen_value:
            chosen_value = max_val
            chosen_boss = b
    return chosen_boss


def parse_open(image, debug=False):
    open_sign = cv2.imread("templates/cn-apocrypha/open sign.png")
    res = cv2.matchTemplate(image, open_sign, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    if debug:
        print(f"Open sign matching value: {max_val}")
    return max_val > 0.7


def parse_apocrypha(image, debug=False):
    image = cv2.imread(image)
    if image is None:
        raise Exception(f"OpenCV can't read {image}")
    battles = {}
    for i in range(1, 4):
        battle = image[31 + (i - 1) * 139 : 169 + (i - 1) * 139, 2:378]
        battles[i] = battle
        if debug:
            cv2.imwrite(f"battle {i}.png", battle)
    output = []
    for battle, battle_image in battles.items():
        if parse_open(battle_image, debug):
            battle_info = {}
            battle_info["boss"] = parse_apoc_boss(battle_image, debug)
            battle_info["hp"] = parse_hp(battle_image, debug)
            output.append(battle_info)
    return output


def parse_summer_race(image, debug=False):
    image = cv2.imread(image)
    if image is None:
        return [{"name": "", "hp": ""}]
    teams_list = [
        t for t in os.listdir(SUMMER_RACE_TEAMS_TEMPLATE) if t.lower().endswith(".png")
    ]
    teams = {}
    for team_template in teams_list:
        team_img = cv2.imread(os.path.join(SUMMER_RACE_TEAMS_TEMPLATE, team_template))
        if team_img is None:
            raise Exception(f"OpenCV can't read {team_template}")
        teams[team_template.split(".")[0]] = team_img
    output = []
    for team, team_img in teams.items():
        res = cv2.matchTemplate(image, team_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if debug:
            print(f"Team: {team}, Matching value: {max_val:.5f}")
        if max_val > 0.8:
            left, top = max_loc
            h, w = team_img.shape[:2]
            right = left + w
            bottom = top + h
            max_height = image.shape[0]
            team_split = team.split("_")
            add_bottom = int(team_split[1])
            team_name = team_split[0]
            hp_img = image[
                min(bottom + add_bottom, max_height) : min(
                    bottom + add_bottom + 50, max_height
                ),
                max(left - 150, 0) : right,
            ]
            team_hp = parse_hp(hp_img, debug)
            output.append({"name": team_name, "hp": team_hp})
    return output


def parse_onigashima(image, debug=False):
    image = cv2.imread(image)
    if image is None:
        return ""
    return parse_hp(image, debug)


if __name__ == "__main__":
    start = time.time()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--image", required=True, help="Input image")
    arg_parser.add_argument(
        "-d", "--debug", action="store_true", help="Write debug images"
    )
    args = arg_parser.parse_args()
    result = parse_summer_race(args.image, args.debug)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(result)
    end = time.time()
    print(f"Finished in {end - start:.5f}s")
