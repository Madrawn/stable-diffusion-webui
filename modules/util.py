import os
import re
from typing import Sequence

from modules import shared
from modules.paths_internal import script_path

# Import VizTracer
from viztracer import VizTracer
from functools import wraps


# Define the decorator
def viztraced(
    tracer_entries: int = 1000000,
    verbose: int = 1,
    max_stack_depth: int = -1,
    exclude_files: Sequence[str] | None = None,
    include_files: Sequence[str] | None = [
        "./extensions",
        "./extensions-builtin",
        "./modules",
        "./repositories",
        "./scripts",
    ],
    ignore_c_function: bool = False,
    ignore_frozen: bool = False,
    log_func_retval: bool = False,
    log_func_args: bool = False,
    log_print: bool = False,
    log_gc: bool = False,
    log_sparse: bool = False,
    log_async: bool = False,
    log_audit: Sequence[str] | None = None,
    pid_suffix: bool = False,
    file_info: bool = True,
    register_global: bool = True,
    trace_self: bool = False,
    min_duration: float = 0,
    minimize_memory: bool = False,
    dump_raw: bool = False,
    sanitize_function_name: bool = False,
    output_file: str = "result.json",
    **kwargs
):
    # This is a wrapper function that takes the original function as an argument
    def wrapper(func):
        # This is the modified function that will be returned by the decorator
        @wraps(func)
        def inner(*args, **kwargs):
            # Create a VizTracer instance with the given parameters
            with VizTracer(
                tracer_entries=tracer_entries,
                verbose=verbose,
                max_stack_depth=max_stack_depth,
                exclude_files=exclude_files,
                include_files=include_files,
                ignore_c_function=ignore_c_function,
                ignore_frozen=ignore_frozen,
                log_func_retval=log_func_retval,
                log_func_args=log_func_args,
                log_print=log_print,
                log_gc=log_gc,
                log_sparse=log_sparse,
                log_async=log_async,
                log_audit=log_audit,
                pid_suffix=pid_suffix,
                file_info=file_info,
                register_global=register_global,
                trace_self=trace_self,
                min_duration=min_duration,
                minimize_memory=minimize_memory,
                dump_raw=dump_raw,
                sanitize_function_name=sanitize_function_name,
                output_file=output_file,
                **kwargs
            ):
                # Start tracing
                # tracer.start()
                # Call the original function and store the result
                result = func(*args, **kwargs)
            # # Stop tracing
            # tracer.stop()
            # # Save the trace data
            # tracer.save()
            # Return the result of the original function
            return result

        # Return the modified function
        return inner

    # Return the wrapper function
    return wrapper


def natural_sort_key(s, regex=re.compile("([0-9]+)")):
    return [int(text) if text.isdigit() else text.lower() for text in regex.split(s)]


def listfiles(dirname):
    filenames = [
        os.path.join(dirname, x) for x in sorted(os.listdir(dirname), key=natural_sort_key) if not x.startswith(".")
    ]
    return [file for file in filenames if os.path.isfile(file)]


def html_path(filename):
    return os.path.join(script_path, "html", filename)


def html(filename):
    path = html_path(filename)

    if os.path.exists(path):
        with open(path, encoding="utf8") as file:
            return file.read()

    return ""


def walk_files(path, allowed_extensions=None):
    if not os.path.exists(path):
        return

    if allowed_extensions is not None:
        allowed_extensions = set(allowed_extensions)

    items = list(os.walk(path, followlinks=True))
    items = sorted(items, key=lambda x: natural_sort_key(x[0]))

    for root, _, files in items:
        for filename in sorted(files, key=natural_sort_key):
            if allowed_extensions is not None:
                _, ext = os.path.splitext(filename)
                if ext not in allowed_extensions:
                    continue

            if not shared.opts.list_hidden_files and ("/." in root or "\\." in root):
                continue

            yield os.path.join(root, filename)


def ldm_print(*args, **kwargs):
    if shared.opts.hide_ldm_prints:
        return

    print(*args, **kwargs)
