# !/usr/bin/env python

import constants
import importlib
import inspect
import itertools as it
import os
import subprocess as sp
import sys
import traceback

from scene.scene import Scene
from utils.sounds import play_error_sound
from utils.sounds import play_finish_sound


def handle_scene(scene, **config):
    import platform
    if config["quiet"]:
        curr_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    if config["show_last_frame"]:
        scene.save_image(mode=config["saved_image_mode"])
    open_file = any([
        config["show_last_frame"],
        config["open_video_upon_completion"],
        config["show_file_in_finder"]
    ])
    if open_file:
        commands = ["open"]
        if (platform.system() == "Linux"):
            commands = ["xdg-open"]
        elif (platform.system() == "Windows"):
            commands = ["start"]

        if config["show_file_in_finder"]:
            commands.append("-R")

        if config["show_last_frame"]:
            commands.append(scene.get_image_file_path())
        else:
            commands.append(scene.get_movie_file_path())
        # commands.append("-g")
        FNULL = open(os.devnull, 'w')
        sp.call(commands, stdout=FNULL, stderr=sp.STDOUT)
        FNULL.close()

    if config["quiet"]:
        sys.stdout.close()
        sys.stdout = curr_stdout


def is_scene(obj):
    if not inspect.isclass(obj):
        return False
    if not issubclass(obj, Scene):
        return False
    if obj == Scene:
        return False
    return True


def prompt_user_for_choice(name_to_obj):
    num_to_name = {}
    names = sorted(name_to_obj.keys())
    for count, name in zip(it.count(1), names):
        print("%d: %s" % (count, name))
        num_to_name[count] = name
    try:
        user_input = input(constants.CHOOSE_NUMBER_MESSAGE)
        return [
            name_to_obj[num_to_name[int(num_str)]]
            for num_str in user_input.split(",")
        ]
    except KeyError:
        print(constants.INVALID_NUMBER_MESSAGE)
        sys.exit()
        user_input = input(constants.CHOOSE_NUMBER_MESSAGE)
        return [
            name_to_obj[num_to_name[int(num_str)]]
            for num_str in user_input.split(",")
        ]


def get_scene_classes(scene_names_to_classes, config):
    if len(scene_names_to_classes) == 0:
        print(constants.NO_SCENE_MESSAGE)
        return []
    if len(scene_names_to_classes) == 1:
        return list(scene_names_to_classes.values())
    if config["scene_name"] in scene_names_to_classes:
        return [scene_names_to_classes[config["scene_name"]]]
    if config["scene_name"] != "":
        print(constants.SCENE_NOT_FOUND_MESSAGE)
        return []
    if config["write_all"]:
        return list(scene_names_to_classes.values())
    return prompt_user_for_choice(scene_names_to_classes)


def get_module(file_name):
    module_name = file_name.replace(".py", "").replace(os.sep, ".")
    return importlib.import_module(module_name)


def main(config):
    module = get_module(config["file"])
    scene_names_to_classes = dict(inspect.getmembers(module, is_scene))

    scene_kwargs = dict([
        (key, config[key])
        for key in [
            "camera_config",
            "frame_duration",
            "skip_animations",
            "write_to_movie",
            "save_pngs",
            "movie_file_extension",
            "start_at_animation_number",
            "end_at_animation_number",
        ]
    ])

    scene_kwargs["name"] = config["output_name"]
    if config["save_pngs"]:
        print("We are going to save a PNG sequence as well...")
        scene_kwargs["save_pngs"] = True
        scene_kwargs["pngs_mode"] = config["saved_image_mode"]

    for SceneClass in get_scene_classes(scene_names_to_classes, config):
        try:
            handle_scene(SceneClass(**scene_kwargs), **config)
            play_finish_sound()
        except Exception:
            print("\n\n")
            traceback.print_exc()
            print("\n\n")
            play_error_sound()


if __name__ == "__main__":
    main()
