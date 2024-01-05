import os
import re
from typing import Sequence

from modules import shared
from modules.paths_internal import script_path, cwd

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

    try:
        with open(path, encoding="utf8") as file:
            return file.read()
    except OSError:
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


def truncate_path(target_path, base_path=cwd):
    abs_target, abs_base = os.path.abspath(target_path), os.path.abspath(base_path)
    try:
        if os.path.commonpath([abs_target, abs_base]) == abs_base:
            return os.path.relpath(abs_target, abs_base)
    except ValueError:
        pass
    return abs_target


class MassFileListerCachedDir:
    """A class that caches file metadata for a specific directory."""

    def __init__(self, dirname):
        self.files = None
        self.files_cased = None
        self.dirname = dirname

        stats = ((x.name, x.stat(follow_symlinks=False)) for x in os.scandir(self.dirname))
        files = [(n, s.st_mtime, s.st_ctime) for n, s in stats]
        self.files = {x[0].lower(): x for x in files}
        self.files_cased = {x[0]: x for x in files}


class MassFileLister:
    """A class that provides a way to check for the existence and mtime/ctile of files without doing more than one stat call per file."""

    def __init__(self):
        self.cached_dirs = {}

    def find(self, path):
        """
        Find the metadata for a file at the given path.

        Returns:
            tuple or None: A tuple of (name, mtime, ctime) if the file exists, or None if it does not.
        """

        dirname, filename = os.path.split(path)

        cached_dir = self.cached_dirs.get(dirname)
        if cached_dir is None:
            cached_dir = MassFileListerCachedDir(dirname)
            self.cached_dirs[dirname] = cached_dir

        stats = cached_dir.files_cased.get(filename)
        if stats is not None:
            return stats

        stats = cached_dir.files.get(filename.lower())
        if stats is None:
            return None

        try:
            os_stats = os.stat(path, follow_symlinks=False)
            return filename, os_stats.st_mtime, os_stats.st_ctime
        except Exception:
            return None

    def exists(self, path):
        """Check if a file exists at the given path."""

        return self.find(path) is not None

    def mctime(self, path):
        """
        Get the modification and creation times for a file at the given path.

        Returns:
            tuple: A tuple of (mtime, ctime) if the file exists, or (0, 0) if it does not.
        """

        stats = self.find(path)
        return (0, 0) if stats is None else stats[1:3]

    def reset(self):
        """Clear the cache of all directories."""
        self.cached_dirs.clear()
