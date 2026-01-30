import os
import re
import sys
import subprocess
import logging
import argparse
import yaml
import fnmatch

from datetime import datetime


INCLUDE_PATH = 'include'  # The range of file paths that should be checked
LICENSE_FILE_NAME = 'LICENSE'  # Default license file name
ALLOWED_LICENSE = 'allowed_licenses'  # List of permitted license notices
ESPRESSIF_COPYRIGHT_FULL = 'espressif_copyright_full'  # Complete Copyright Statement Template
ESPRESSIF_COPYRIGHT_SHORT = 'espressif_copyright_short'  # Simple Copyright Statement Template
LICENSE_FOR_NEW_FILES = 'license_for_new_files'  # Specifies the license name that new files should use


LOG_LEVELS = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG
}


def print_debug(message):
    logging.debug(f"\033[37m{message}\033[0m")


def print_info(message):
    logging.info(f"\033[37m{message}\033[0m")


def print_warning(message):
    logging.warning(f"\033[33m{message}\033[0m")


def print_error(message):
    logging.error(f"\033[31m{message}\033[0m")


class LicenseChecker:
    """
    Used to check whether the LICENSE and copyright declaration of newly added files
    comply with company specifications, and automatically fix non-compliant content
    based on configuration.
    """
    def __init__(self, config_path = 'check_copyright_config.yaml', file = [], replace = False):
        """
        Initialize the checker instance.

        Args:
            config_path (str): Path to the YAML configuration file.
            file (List[str]): List of file paths to check.
            replace (bool): Whether to enable automatic fixing.
        """
        self.config = self.load_config(config_path)
        self.job_config = ''
        self.new_file = file
        self.replace = replace
        self.current_year = datetime.now().year
        self.valid_extensions = {'.c', '.cpp', '.h', '.cc', '.hpp', '.hxx', '.hh'}
        self.check_result = True
        self.invalid_license_file_set = set()
        self.invalid_copyright_full_set = set()
        self.invalid_copyright_short_set = set()


    def load_config(self, config_path='check_copyright_config.yaml'):
        """
        Load configuration from a YAML file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            dict: Configuration contents (rules for each job name).
        """
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config


    def print_copyright(self):
        """
        Print standard LICENSE and copyright templates for reference.
        """
        for job_name, job_config in self.config.items():
            # self.process_job(job_name, job_config)
            if job_name != 'ignore':
                espressif_copyright_full = job_config.get(ESPRESSIF_COPYRIGHT_FULL, 'Default Full').format(license=job_config[LICENSE_FOR_NEW_FILES], year=self.current_year)
                espressif_copyright_short = job_config.get(ESPRESSIF_COPYRIGHT_SHORT, 'Default Short').format(license=job_config[LICENSE_FOR_NEW_FILES], year=self.current_year)
                include = job_config.get(INCLUDE_PATH, '')
                print_info(f"Processing job: {job_name}")
                print_warning(f"The content of the LICENSE file under this path should be as follows: {include}")
                print_warning(f"Espressif LICENSE file:")
                print_info(f"{self.format_license_file(espressif_copyright_full).strip()}\n")
                print_warning(f"Espressif Copyright Full:")
                print_info(f"{espressif_copyright_full}")
                print_warning(f"Espressif Copyright Short:")
                print_info(f"{espressif_copyright_short}")
                print_warning('-' * 50)


    def get_invalid_license_file_set(self):
        return self.invalid_license_file_set


    def get_invalid_copyright_full_set(self):
        return self.invalid_copyright_full_set


    def get_invalid_copyright_short_set(self):
        return self.invalid_copyright_short_set


    def get_commit_file(self):
        """
        Get newly added files from the current commit (via `git diff`).

        Returns:
            list[str]: List of added file paths.
        """
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-status', 'HEAD~1', 'HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            new_files = [
                line.split('\t')[1]
                for line in result.stdout.splitlines()
                if line.startswith('A')
            ]
            return new_files
        except subprocess.CalledProcessError as e:
            print_error(f"Error occurred while retrieving newly added files: {e}")
            sys.exit(1)


    def get_file_in_directory(self, directory):
        """
        Get all source code files with valid extensions under the directory.

        Args:
            directory (str): Path to the directory.

        Returns:
            list[str]: List of file paths.
        """
        file_paths = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Get the extension and convert it to lowercase
                file_extension = os.path.splitext(file)[1].lower()
                if file_extension in self.valid_extensions:
                    file_paths.append(os.path.join(root, file))
        return file_paths


    def get_config(self, config, target_file_path):
        """
        Get the rule configuration that matches a specific file path.

        Args:
            config (dict): All configuration data.
            target_file_path (str): File path to match.

        Returns:
            dict or None: Matched rule configuration.
        """
        # First check the DEFAULT section, returning to the global configuration
        default_config = config.get('DEFAULT', {})

        # Traverse other rule parts
        for rule_name, rule_data in config.items():
            if rule_name == 'DEFAULT':
                continue

            include_path = rule_data.get(INCLUDE_PATH, [])
            # If target_file_path matches any include path, return the configuration of that rule
            for path_index in include_path:
                if fnmatch.fnmatch(target_file_path, path_index):
                    # Check if it is in the list of ignored files
                    if rule_name == 'ignore':
                        return None
                    else:
                        default_config = self.merge_configs(default_config, rule_data)

        return default_config


    def generate_license_text(self, license_name, copyright_template):
        """
        Generate the formatted license text.
        """
        formatted_copyright = copyright_template.format(license=license_name, year=self.current_year)
        indented_copyright = '\n'.join(f'{line}' for line in formatted_copyright.splitlines())
        license_text = f"""{indented_copyright}"""
        return license_text


    def merge_configs(self, default_config, special_config):
        """
        Merge the DEFAULT and specific job configuration, prioritizing job settings.

        Returns:
            dict: Merged configuration.
        """
        merged_config = {}

        for key, value in default_config.items():
            merged_config[key] = value

        for key, value in special_config.items():
            # The value in the rule configuration will override the value in the default configuration
            merged_config[key] = value

        return merged_config


    def format_license_file(self, input_string):
        """
        Format the LICENSE template (remove the first three characters of each line).

        Args:
            input_string (str): Original template string.

        Returns:
            str: Processed LICENSE content.
        """
        lines = input_string.splitlines()

        # Remove the first three characters from each line
        modified_lines = [line[3:] if len(line) > 3 else '' for line in lines]

        # Rejoin the processed lines into a new string
        return '\n'.join(modified_lines)


    def check_license_file(self, file_path):
        """
        Check whether a LICENSE file exists and whether the content matches the template.

        Args:
            file_path (str): Path to a source file (used to search upward for LICENSE).

        Returns:
            bool: Whether it matches the requirements.
        """
        exit_flag = False  # Marks whether to match any include path
        current_dir = os.path.dirname(file_path)
        expect_license = self.job_config.get(LICENSE_FOR_NEW_FILES, '')
        include_path = self.job_config.get(INCLUDE_PATH, [])

        while current_dir != os.path.dirname(current_dir):  # 循环直到到达根目录
            license_path = os.path.join(current_dir, LICENSE_FILE_NAME)

            if os.path.isfile(license_path):
                if license_path not in self.invalid_license_file_set:
                    print_debug(f"Found LICENSE file at: {license_path}")
                    with open(license_path, 'r', encoding='utf-8') as f:
                        license_file = f.read()

                    # Check that the LICENSE content contains the expected license notice
                    if expect_license in license_file:
                        print_debug(f"LICENSE file in {current_dir} matches expected license: {expect_license}")

                        # Check if the copyright format is correct
                        expect_copyright = self.format_license_file(
                            self.job_config[ESPRESSIF_COPYRIGHT_FULL]
                        ).strip()

                        expect_copyright = expect_copyright.format(license=expect_license, year=self.current_year)
                        if expect_copyright.strip() == license_file.strip():
                            print_debug(f"LICENSE file format of {license_path} is correct.")
                        else:
                            print_debug(f"LICENSE file format of {license_path} is incorrect.")
                            self.invalid_license_file_set.add(license_path)
                            self.check_result = False
                        return True
                    else:
                        print_warning(f"LICENSE in {current_dir} does not match expected license.")
                        return False

            if exit_flag:
                break

            # Check if it is the root directory of the Git repository, and stop searching if it is
            if os.path.isdir(os.path.join(current_dir, '.git')):
                print_debug(f"Reached git repo at {current_dir}. Stopping search.")
                break

            # If not in the include list, exit
            if not all(fnmatch.fnmatch(current_dir, path_index) for path_index in include_path):
                exit_flag = True

            # Move up one directory
            current_dir = os.path.dirname(current_dir)

        print_debug("No LICENSE file found in any parent directory.")
        return False


    def replace_copyright(self, file_path):
        """
        Automatically replace the copyright declaration
        (including LICENSE files and comment blocks in source files).

        Args:
            file_path (str): Target file path.
        """
        copyright_type, copyright_pattern = self.get_copyright_pattern(file_path)
        if copyright_pattern is not None:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                if os.path.basename(file_path) == LICENSE_FILE_NAME:
                    # Check if the copyright format is correct
                    expect_license = self.job_config.get(LICENSE_FOR_NEW_FILES, '')
                    expect_copyright = self.format_license_file(
                        self.job_config[ESPRESSIF_COPYRIGHT_FULL]
                    ).strip()
                    expect_copyright = expect_copyright.format(license=expect_license, year=self.current_year)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(expect_copyright + "\n")
                    print_warning(f"Replaced incorrect license in: {file_path}")
                else:
                    # Matches a multi-line comment copyright notice
                    re_multi_line_comment = re.compile(r'[\s\S]?/\*[\s\S]*?\*/')

                    # Check for and replace copyright notices that are multi-line comments
                    if re.match(re_multi_line_comment, content):
                        print_debug(f"Replaced multi-line copyright declaration in {file_path}.")
                        content = re.sub(re_multi_line_comment, f'{copyright_pattern}', content, count=1)
                    else:
                        print_warning(f"Add copyright declaration found at the beginning of {file_path}.")
                        content = f'{copyright_pattern}\n' + content

                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)

            except FileNotFoundError:
                print_error(f"{file_path} not found.")
            except Exception as e:
                print_error(f"Error processing {file_path}: {e}")


    def get_copyright_pattern(self, file_path):
        """
        Get the copyright template corresponding to a file.

        Returns:
            tuple[bool, str]: Whether SHORT mode is used, and the template string.
        """
        self.job_config = self.get_config(self.config, file_path)  # 通过get_config函数获取相应的配置

        if self.job_config is None:
            return None, None

        copyright_type = self.check_license_file(file_path)
        if copyright_type:
            copyright_pattern = self.job_config[ESPRESSIF_COPYRIGHT_SHORT].format(license=self.job_config[LICENSE_FOR_NEW_FILES], year=self.current_year)
        else:
            copyright_pattern = self.job_config[ESPRESSIF_COPYRIGHT_FULL].format(license=self.job_config[LICENSE_FOR_NEW_FILES], year=self.current_year)

        copyright_pattern = copyright_pattern.strip()
        return copyright_type, copyright_pattern


    def check_copyright(self, file_path):
        """
        Check if the copyright declaration at the top of a file is compliant.

        Returns:
            bool: Whether it's compliant.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

                copyright_type, copyright_pattern = self.get_copyright_pattern(file_path)
                if copyright_pattern is not None:
                    copyright_pattern_escape = re.escape(copyright_pattern)  # 对版权声明进行转义以便匹配

                    # Check that the license statement is correct
                    for license_name in self.job_config[ALLOWED_LICENSE]:
                        license_pattern = re.escape(license_name)
                        if re.search(license_pattern, content):
                            break
                    else:
                        print_error(f"The license declaration format of {file_path} is incorrect")
                        if copyright_type:
                            self.invalid_copyright_short_set.add(file_path)
                        else:
                            self.invalid_copyright_full_set.add(file_path)
                        return False

                    license_for_new_files = self.job_config[LICENSE_FOR_NEW_FILES]
                    # Modification: Allow spaces or - to connect words
                    license_for_new_files = license_for_new_files.replace(" ", r"[\s-]")  # 允许空格或 - 作为连接符

                    # Check that the license in the file matches and the copyright notice is in place
                    if re.search(license_for_new_files, content):
                        if not re.search(copyright_pattern_escape, content, re.DOTALL):
                            print_debug(f"The copyright declaration format of {file_path} is incorrect")
                            if copyright_type:
                                self.invalid_copyright_short_set.add(file_path)
                            else:
                                self.invalid_copyright_full_set.add(file_path)
                            return False

        except FileNotFoundError:
            print_error(f"{file_path} file not found")
            return False
        except Exception as e:
            print_warning(f"Error occurred while checking {file_path}: {e}")
            return False

        return True


    def process(self):
        """
        Main process: handles the list of input files, performs checks or replacements.
        """
        if not self.new_file:
            # Get a list of newly added files in the current commit
            self.new_file = get_commit_file()

        if not self.new_file:
            print_error("There are no new files in the current commit.")
            sys.exit(0)

        for file_path in self.new_file:
            # Check if the path is a folder
            if os.path.isdir(file_path):
                # If it is a folder, get all the files in the folder
                print_debug(f"Processing directory: {file_path}")
                new_files_in_dir = self.get_file_in_directory(file_path)
                for new_file in new_files_in_dir:
                    if not self.check_copyright(new_file):
                        self.check_result = False
            elif os.path.isfile(file_path):
                # Check if the file extension is in the list of supported extensions
                if any(file_path.endswith(ext) for ext in self.valid_extensions):
                    if not self.check_copyright(file_path):
                        self.check_result = False

                # If it is a LICENSE file, get all supported file extensions in the directory
                elif os.path.basename(file_path) == LICENSE_FILE_NAME:
                    print_debug(f"Found LICENSE file in {root}. Now checking files with extensions {self.valid_extensions} in this directory.")
                    if not self.check_copyright(file_path):
                        self.check_result = False


        if self.get_invalid_license_file_set():
            print_error("The following files need to be formatted according to the LICENSE file template:")
            for file_path in self.invalid_license_file_set:
                print_info(f" - {file_path}")
                if self.replace:
                    self.replace_copyright(file_path)
        if self.get_invalid_copyright_full_set():
            print_error("The following files need to be formatted according to the {ESPRESSIF_COPYRIGHT_FULL} template:")
            for file_path in self.invalid_copyright_full_set:
                print_info(f" - {file_path}")
                if self.replace:
                    self.replace_copyright(file_path)
        if self.get_invalid_copyright_short_set():
            print_error("The following files need to be formatted according to the {ESPRESSIF_COPYRIGHT_SHORT} template:")
            for file_path in self.invalid_copyright_short_set:
                print_info(f" - {file_path}")
                if self.replace:
                    self.replace_copyright(file_path)


def main():
    parser = argparse.ArgumentParser(description="Check the copyright declaration of newly added files.")
    parser.add_argument(
        '--config',
        default = 'check_copyright_config.yaml',
        type = str,
        help = 'Configuration file path'
    )
    parser.add_argument(
        '--replace',
        action = 'store_true',
        help = 'Enable replacement functionality'
    )
    parser.add_argument(
        '-v', '--verbose',
        action = 'count',
        default = 1,
        help="Increase the log verbosity, use -v, -vv, etc. to set"
    )

    parser.add_argument('file', nargs = '+', help = "Input file list")

    args = parser.parse_args()

    logging.basicConfig(
        level = LOG_LEVELS[min(args.verbose, 2)],  # Limit the maximum log level to DEBUG
        format = '%(message)s'
    )

    checker = LicenseChecker(config_path=args.config, file = args.file, replace=args.replace)

    checker.process()

    if checker.check_result == False:
        print_warning("The correct license format is as follows:")
        checker.print_copyright()
    else:
        print_info("Good job! All files have the correct license format.")

    sys.exit(0 if checker.check_result else 1)


if __name__ == "__main__":
    main()
