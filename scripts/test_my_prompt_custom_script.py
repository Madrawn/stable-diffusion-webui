import random
from modules.shared import opts
from modules.processing import process_images, images
from PIL import ImageFont, ImageDraw
from modules.paths_internal import roboto_ttf_file
import modules.scripts as scripts
import gradio as gr
from collections import namedtuple
from random import randint


class Script(scripts.Script):
    GridSaveFlags = namedtuple(
        "GridSaveFlags",
        ["never_grid", "always_grid", "always_save_grid"],
        defaults=(False, False, False),
    )
    grid_options_mapping = {
        "Use user settings": GridSaveFlags(),
        "Don't generate": GridSaveFlags(never_grid=True),
        "Generate": GridSaveFlags(always_grid=True),
        "Generate and always save": GridSaveFlags(
            always_grid=True, always_save_grid=True
        ),
    }
    default_grid_opt = list(grid_options_mapping.keys())[-1]

    def title(self):
        return "Test my prompt!"

    def ui(self, is_img2img):
        neg_pos = gr.Dropdown(
            label="Test negative or positive",
            choices=["Positive", "Negative"],
            value="Positive",
        )
        action = gr.Radio(
            label="Action",
            choices=["Remove", "Attention", "Wrap in", "Stack"],
            value="Remove",
        )
        with gr.Column(visible=False) as att:
            attention_strength = gr.Slider(
                minimum=-2, maximum=2, step=0.1, label="Attention Strength", value=1.4
            )
        with gr.Column(visible=False) as wrap:
            prefix = gr.Textbox(label="Before prompt", lines=1, value="(")
            suffix = gr.Textbox(label="after prompt", lines=1, value=")")

        with gr.Column(visible=False) as stack:
            reverse = gr.Checkbox(label="Reversed", value=False)
            shuffle = gr.Checkbox(label="Shuffle", value=False)

        def update_visible(action_type):
            return [
                gr.update(visible=action_type == "Attention"),
                gr.update(visible=action_type == "Wrap in"),
                gr.update(visible=action_type == "Stack"),
            ]

        action.change(update_visible, action, [att, wrap, stack])
        skip_x_first = gr.Slider(
            minimum=0, maximum=32, step=1, label="Skip X first words", value=0
        )
        group_x = gr.Slider(
            minimum=1, maximum=32, step=1, label="Group X words", value=1
        )
        separator = gr.Textbox(label="Separator used", lines=1, value=", ")
        grid_option = gr.Radio(
            choices=list(self.grid_options_mapping.keys()),
            label="Grid generation",
            value=self.default_grid_opt,
        )
        font_size = gr.Slider(
            minimum=12, maximum=64, step=1, label="Font size", value=32
        )
        return [
            neg_pos,
            skip_x_first,
            separator,
            grid_option,
            font_size,
            action,
            group_x,
            reverse,
            attention_strength,
            prefix,
            suffix,
            shuffle,
        ]

    def apply_action(
        self,
        action,
        separator,
        grouped_prompt_array,
        f,
        reverse,
        attention_strength,
        prefix,
        suffix,
        shuffle,
    ):
        if action == "Remove":
            return self.remove_action(
                separator,
                grouped_prompt_array,
                f,
            )
        if action == "Attention":
            return self.attention_action(
                separator, grouped_prompt_array, f, attention_strength
            )
        if action == "Wrap in":
            return self.wrap_action(
                separator,
                grouped_prompt_array,
                f,
                prefix,
                suffix,
            )
        if action == "Stack":
            return self.stack_action(
                separator, grouped_prompt_array, f, reverse, shuffle
            )

    def run(
        self,
        p,
        neg_pos,
        skip_x_first,
        separator,
        grid_option,
        font_size,
        action,
        group_x: int,
        reverse,
        attention_strength,
        prefix,
        suffix,
        shuffle,
    ):
        def write_on_image(img, msg):
            ix, iy = img.size
            draw = ImageDraw.Draw(img)
            margin = 2
            fontsize = font_size
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(roboto_ttf_file, fontsize)
            text_height = iy - 60
            tx = draw.textbbox((0, 0), msg, font)
            draw.text(
                (int((ix - tx[2]) / 2), text_height + margin), msg, (0, 0, 0), font=font
            )
            draw.text(
                (int((ix - tx[2]) / 2), text_height - margin), msg, (0, 0, 0), font=font
            )
            draw.text(
                (int((ix - tx[2]) / 2 + margin), text_height), msg, (0, 0, 0), font=font
            )
            draw.text(
                (int((ix - tx[2]) / 2 - margin), text_height), msg, (0, 0, 0), font=font
            )
            draw.text(
                (int((ix - tx[2]) / 2), text_height), msg, (255, 255, 255), font=font
            )
            return img

        p.do_not_save_samples = True
        initial_seed = p.seed
        if initial_seed == -1:
            initial_seed = randint(1000000, 9999999)
        if neg_pos == "Positive":
            initial_prompt: str = p.prompt
            prompt_array: str = p.prompt
        else:
            initial_prompt: str = p.negative_prompt
            prompt_array: str = p.negative_prompt

        def split_array(arr, skip_x_first):
            first_part = arr[:skip_x_first]
            second_part = arr[skip_x_first:]
            return first_part, second_part

        skipped_prompt, prompt_array = split_array(
            prompt_array.split(separator), skip_x_first
        )
        grouped_prompt_array = [
            separator.join(prompt_array[i : i + group_x])
            for i in range(0, len(prompt_array), group_x)
        ]
        print("total images :", len(grouped_prompt_array))
        for g in range(len(grouped_prompt_array) + 1):
            f = g - 1
            new_prompt = (
                separator.join(
                    (
                        separator.join(skipped_prompt),
                        self.apply_action(
                            action,
                            separator,
                            [*grouped_prompt_array],
                            f,
                            reverse,
                            attention_strength,
                            prefix,
                            suffix,
                            shuffle,
                        ),
                    )
                )
                if skipped_prompt
                else self.apply_action(
                    action,
                    separator,
                    [*grouped_prompt_array],
                    f,
                    reverse,
                    attention_strength,
                    prefix,
                    suffix,
                    shuffle,
                )
            )

            if neg_pos == "Positive":
                p.prompt = new_prompt
            else:
                p.negative_prompt = new_prompt
            p.seed = initial_seed
            if g == 0:
                proc = process_images(p)
            else:
                appendimages = process_images(p)
                proc.images.insert(0, appendimages.images[0])
                proc.infotexts.insert(0, appendimages.infotexts[0])
            if f >= 0:
                proc.images[0] = write_on_image(
                    proc.images[0], f"{action} " + grouped_prompt_array[f]
                )
            else:
                proc.images[0] = write_on_image(proc.images[0], "full prompt")

            if opts.samples_save:
                images.save_image(
                    proc.images[0],
                    p.outpath_samples,
                    "",
                    proc.seed,
                    proc.prompt,
                    opts.samples_format,
                    info=proc.info,
                    p=p,
                )

        grid_flags = self.grid_options_mapping[grid_option]
        unwanted_grid_because_of_img_count = (
            len(proc.images) < 2 and opts.grid_only_if_multiple
        )
        if (
            (opts.return_grid or opts.grid_save)
            and not p.do_not_save_grid
            and not grid_flags.never_grid
            and not unwanted_grid_because_of_img_count
        ) or grid_flags.always_grid:
            grid = images.image_grid(proc.images)
            proc.images.insert(0, grid)
            proc.infotexts.insert(0, proc.infotexts[-1])
            if opts.grid_save or grid_flags.always_save_grid:
                images.save_image(
                    grid,
                    p.outpath_grids,
                    "grid",
                    initial_seed,
                    initial_prompt,
                    opts.grid_format,
                    info=proc.info,
                    short_filename=not opts.grid_extended_filename,
                    p=p,
                    grid=True,
                )
        return proc

    def remove_action(self, separator, prompt_array, f):
        if f >= 0:
            new_prompt = separator.join(
                [prompt_array[x] for x in range(len(prompt_array)) if x is not f]
            )
        else:
            new_prompt = separator.join(prompt_array)
        return new_prompt

    def stack_action(self, separator, prompt_array, f, reverse, shuffle):
        if f == 0:
            return ""
        elif f > 0:
            if shuffle:
                random.shuffle(prompt_array)
            print(prompt_array)
            new_prompt = separator.join(
                (prompt_array[-f:] if reverse else prompt_array[:f])
            )
            print(new_prompt)
        else:
            new_prompt = separator.join(prompt_array)
        return new_prompt

    def attention_action(self, separator, prompt_array, f, attention_strength):
        if f >= 0:
            new_prompt = separator.join(
                [
                    (
                        f"({prompt_array[x]}:{attention_strength})"
                        if x == f
                        else prompt_array[x]
                    )
                    for x in range(len(prompt_array))
                ]
            )
        else:
            new_prompt = separator.join(prompt_array)
        return new_prompt

    def wrap_action(self, separator, prompt_array, f, prefix, suffix):
        if f >= 0:
            new_prompt = separator.join(
                [
                    f"{prefix}{prompt_array[x]}{suffix}" if x == f else prompt_array[x]
                    for x in range(len(prompt_array))
                ]
            )
        else:
            new_prompt = separator.join(prompt_array)
        return new_prompt
