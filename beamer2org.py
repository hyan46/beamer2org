#!/usr/bin/env python

import os
import sys
import re
def format_text(text):
    """
    Formats text for bold, underline, and italic in org-mode, handling nested structures and trailing spaces.

    Args:
    text (str): String to be formatted.

    Returns:
    str: Formatted string.
    """
    formats = [
        (r'\\textbf\{([^{}]*)\}', '*', '*'),
        (r'\\uline\{([^{}]*)\}', '_', '_'),
        (r'\\italic\{([^{}]*)\}', '/', '/')
    ]

    replacements_made = True

    while replacements_made:
        replacements_made = False
        for pattern, org_start, org_end in formats:
            while re.search(pattern, text):
                # Process each match separately
                match = re.search(pattern, text)
                if match:
                    content = match.group(1)
                    # Check for trailing space in the content
                    if content.endswith(' '):
                        content = content[:-1]
                        replacement = org_start + content + org_end + ' '
                    else:
                        replacement = org_start + content + org_end
                    text = text[:match.start()] + replacement + text[match.end():]
                    replacements_made = True

    return text



# Testing the updated script section with the provided LaTeX lines


# Define the updated part of the script for handling graphics

def process_graphics(stripped_line, indent_level, latex_file_dir):
    org_output = []
    if r'\includegraphics' in stripped_line:
        # Extract graphic relative path without extension
        graphic_relative_path_without_ext = stripped_line[stripped_line.find('{')+1:stripped_line.find('}')]

        # Construct full path for existence check
        graphic_full_path = os.path.join(latex_file_dir, graphic_relative_path_without_ext)

        # Check for possible image extensions
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp','.pdf']
        file_exists = False
        for ext in extensions:
            if os.path.exists(graphic_full_path + ext):
                graphic_relative_path = graphic_relative_path_without_ext + ext
                file_exists = True
                break

        if not file_exists:
            print(f"Warning: Image file '{graphic_full_path}' does not exist.")
            return org_output  # Return empty output if file does not exist

        # Extract width and height attributes
        attrs = ''
        width_index = stripped_line.find('width=')
        if width_index != -1:
            width_end = stripped_line.find(']', width_index)
            width = stripped_line[width_index + len('width='):width_end].split()[0]
            attrs += ' :width ' + width.strip()

        height_index = stripped_line.find('height=')
        if height_index != -1:
            height_end = stripped_line.find(']', height_index)
            height = stripped_line[height_index + len('height='):height_end].split()[0]
            attrs += ' :height ' + height.strip()

        # Add indentation and use relative path in org output
        indent_spaces = ' ' * (indent_level * 2)
        org_output.append(indent_spaces + '#+attr_latex:' + attrs)
        org_output.append(indent_spaces + '[[file:' + graphic_relative_path + ']]')

    return org_output

def process_equations(latex_input):
    org_output = []
    in_equation = False
    equation_start_found = False
    current_delimiter = ""

    # Define pairs of equation delimiters
    delimiter_pairs = {
        r'\[': r'\]',
        r'\(': r'\)',
        r'$$': r'$$',  # Assuming $$ is used for both start and end
        # Add more delimiters here if needed
    }

    for line in latex_input:
        stripped_line = line.strip()

        if in_equation:
            if delimiter_pairs[current_delimiter] in stripped_line:
                in_equation = False
                # Append the end delimiter to the last line of actual equation content
                org_output[-1] = org_output[-1] + ' ' + delimiter_pairs[current_delimiter]
            else:
                if not equation_start_found:
                    # Append the start delimiter to the first line of actual equation content
                    org_output.append(current_delimiter + ' ' + stripped_line)
                    equation_start_found = True
                else:
                    org_output.append(stripped_line)
        else:
            # Check for the start of an equation
            for start_delimiter, end_delimiter in delimiter_pairs.items():
                if start_delimiter in stripped_line:
                    in_equation = True
                    current_delimiter = start_delimiter
                    equation_start_found = False
                    break
            if not in_equation:
                org_output.append(stripped_line)

    return org_output





def process_section(stripped_line):
    if stripped_line.startswith(r'\section'):
        section_name = stripped_line[stripped_line.find('{')+1:stripped_line.find('}')]
        return ['* ' + section_name, 1]  # Returns list with section line and new section level
    elif stripped_line.startswith(r'\subsection'):
        subsection_name = stripped_line[stripped_line.find('{')+1:stripped_line.find('}')]
        return ['** ' + subsection_name, 2]  # Returns list with subsection line and new section level
    return [], 0  # Returns empty list and 0 if not a section or subsection



def add_closing_heading_if_needed(org_output, latex_input, current_index, header_level_count):
    special_env_starters = [r'\begin{block}', r'\begin{theorem}', r'\begin{proof}', r'\begin{prop}', r'\begin{prop*}', r'\begin{thm*}']

    for i in range(current_index + 1, len(latex_input)):
        next_line = latex_input[i].strip()

        # Ignore empty lines and comment lines
        if not next_line or next_line.startswith('%'):
            continue

        # Check for the end of the frame or start of another special environment
        if next_line.startswith(r'\end{frame}') or any(next_line.startswith(env) for env in special_env_starters) or next_line.count(r'\includegraphics') == 2:
            break

        # If we find substantive content, add a closing heading
        if next_line.startswith(r'\item') or next_line:
            closing_header_level = '*' * (header_level_count + 1)
            org_output.extend([
                f"{closing_header_level} Empty Title :B_ignoreheading:",
                ":PROPERTIES:",
                ":BEAMER_env: ignoreheading",
                ":END:"
            ])
            break

def extract_title(command, default_title=""):
    """
    Extracts the title from a LaTeX command like \title{title}.
    Handles cases where the title contains additional LaTeX commands or symbols.

    Args:
    command (str): A LaTeX command string.

    Returns:
    str: The extracted title.
    """
    start = command.find('{') + 1
    end = command.rfind('}')  # Use rfind to get the index of the last '}'
    return command[start:end].strip() if start < end else default_title


def process_header(stripped_line, org_output, title):
    org_output.append(f'#+TITLE: {title}')
    org_output.extend([
        '#+filetags: :Presentation:',
        '#+BEAMER_THEME: CambridgeUS',
        '#+BEAMER_COLOR_THEME: default',
        '#+LANGUAGE:  en',
        '#+LaTeX_CLASS_OPTIONS: [presentation]',
        '#+EXCLUDE_TAGS: noexport',
        '#+COLUMNS: %40ITEM %10BEAMER_env(Env) %9BEAMER_envargs(Env Args) %4BEAMER_col(Col) %10BEAMER_extra(Extra)',
        '#+OPTIONS:   H:2 num:t toc:t \\n:nil @:t ::t |:t ^:t -:t f:t *:t <:t',
        '#+OPTIONS:   TeX:t LaTeX:t skip:nil d:nil todo:t pri:nil tags:not-in-toc',
        '#+LATEX: \\AtBeginSection{\\frame{\\sectionpage}}'
    ])


# Writing a function to handle the specific case of two images on the same line in LaTeX and converting it to org-mode format
def process_two_images_on_same_line(stripped_line, header_level_count):
    org_output = []

    # Split the line into two parts for each image
    parts = stripped_line.split(r'\includegraphics')
    parts = [part.strip() for part in parts if part.strip()]

    if len(parts) != 2:
        return org_output  # Return empty if not two parts

    for i, part in enumerate(parts):
        # Extract the width and image path
        width_start = part.find('width=') + 6
        width_end = part.find('}', width_start)
        width = part[width_start:width_end].split()[0]

        path_start = part.find('{') + 1
        path_end = part.find('}', path_start)
        image_path = part[path_start:path_end]
        if not image_path.endswith('.png'):
            image_path += '.png'

        col_name = "Col left" if i == 0 else "Col right"
        col_width = "0.49" if i == 0 else "0.48"

        # Constructing the org-mode format for each image
        org_output.append(f'{"*" * (header_level_count + 1)} {col_name} :BMCOL:')
        org_output.append(':PROPERTIES:')
        org_output.append(f':BEAMER_col: {col_width}')
        org_output.append(':END:')
        org_output.append('#+ATTR_LATEX: :width 1\\linewidth')
        org_output.append(f'[[file:{image_path}]]')
        

    return org_output



def convert_latex_to_org(latex_input,latex_file_dir):
    '''
    Converts LaTeX to org-mode format with specific headers and handling for sections, subsections, frames, environments, and comments.

    Args:
    latex_input (list of str): List of strings, each representing a line of LaTeX input.

    Returns:
    list of str: List of strings, each representing a line of org-mode output.
    '''
    latex_input = process_equations(latex_input)
    org_output = []
    title = ""
    section_level = 0
    in_frame = False
    in_special_env = False
    indent_level = 0  # Tracks the current level of indentation within a frame
    header_removed = False

    env_types = ['block', 'theorem', 'proof', 'prop', 'prop*','thm*','thm']

    for i, line in enumerate(latex_input):
        stripped_line = line.strip()
        stripped_line = format_text(stripped_line)

        # Skip centering given it is by default
        if stripped_line.startswith(r'\begin{center}') or stripped_line.startswith(r'\end{center}'):
            continue
        
        # Skip figure begin and end commands
        if stripped_line.startswith(r'\begin{figure}') or stripped_line.startswith(r'\end{figure}'):
            continue
        

        # Extract Title
        if stripped_line.startswith(r'\title'):
            title = extract_title(stripped_line, "Untitled Presentation")
            continue

        # Add headers
        if not header_removed:
            if stripped_line.startswith(r'\section'):
                header_removed = True
                process_header(stripped_line, org_output, title)
            else:
                continue


        # Remove comments and end document
        if stripped_line.startswith('%') or stripped_line.startswith(r'\end{document}'):
            continue
        
        # Handle sections and subsections
        if stripped_line.startswith(r'\section'):
            section_name = stripped_line[stripped_line.find('{')+1:stripped_line.find('}')]
            org_output.append('* ' + section_name)
            section_level = 1
            continue
        elif stripped_line.startswith(r'\subsection'):
            subsection_name = stripped_line[stripped_line.find('{')+1:stripped_line.find('}')]
            org_output.append('** ' + subsection_name)
            section_level = 2
            continue

        # Handle frames
        if stripped_line.startswith(r'\begin{frame}'):
            first_brace_index = stripped_line.find('{')
            frame_title_start = stripped_line.find('{', first_brace_index + 1) + 1
            frame_title_end = stripped_line.rfind('}')
            frame_title = stripped_line[frame_title_start:frame_title_end].strip() if frame_title_start < frame_title_end else ""

            header_level_count = max(section_level, 1) + 1
            header_level = '*' * header_level_count
            org_output.append(header_level + ' ' + frame_title)
            in_frame = True
            indent_level = 0  # Reset indent level at the beginning of a frame
            continue
        elif stripped_line.startswith(r'\end{frame}'):
            in_frame = False
            # Add an empty line at the end of the slide
            org_output.append('')            
            continue

        # Process content inside frames
        if in_frame:

            if any(stripped_line.startswith(r'\begin{' + env) for env in env_types):
                env_type = next(env for env in env_types if stripped_line.startswith(r'\begin{' + env))
                # Map 'prop' and 'prop*' to 'theorem' for org-mode
                if env_type in ['prop', 'prop*','thm*','thm']:
                    env_type = 'theorem'
                # title_name = stripped_line[stripped_line.rfind('{')+1:stripped_line.rfind('}')]

                title_name = env_type.capitalize()  # Default title to env_type if not provided
                if stripped_line.count('{') == 2:  # Two '{' indicates a title is provided
                    title_name = stripped_line[stripped_line.rfind('{')+1:stripped_line.rfind('}')]

                header_level_count += 1
                header_level = '*' * header_level_count  # Next level header
                org_output.append(header_level + ' ' + title_name + " :B_" + env_type + ":")
                org_output.append(':PROPERTIES:')
                org_output.append(f':BEAMER_env: {env_type}')
                org_output.append(':END:')
                in_special_env = True
                indent_level = 0
                continue
            elif any(stripped_line.startswith(r'\end{' + env) for env in env_types):
                in_special_env = False
                header_level_count -= 1
                add_closing_heading_if_needed(org_output, latex_input, i, header_level_count)
                continue



            # # Handle graphics within frames with the same indent level
            # if r'\includegraphics' in stripped_line:
            #      graphics_output = process_graphics(stripped_line, indent_level)
            #      org_output.extend(graphics_output)
            #      continue

            # Check for lines with two \includegraphics commands
            if stripped_line.count(r'\includegraphics') == 2:
                org_output.extend(process_two_images_on_same_line(stripped_line, header_level_count))
                in_special_env = True
                add_closing_heading_if_needed(org_output, latex_input, i, header_level_count)
                continue

            


            # Process single graphic
            if r'\includegraphics' in stripped_line:
                org_output.extend(process_graphics(stripped_line, indent_level,latex_file_dir))
                continue
            

            # Increase or decrease the indent level for itemize/enumerate
            if stripped_line.startswith(r'\begin{itemize}') or stripped_line.startswith(r'\begin{enumerate}'):
                indent_level += 1
                continue
            elif stripped_line.startswith(r'\end{itemize}') or stripped_line.startswith(r'\end{enumerate}'):
                indent_level -= 1
                continue

            # Convert \item lines
            if stripped_line.startswith(r'\item'):
                indent_spaces = ' ' * ((indent_level - 1) * 2)
                org_line = indent_spaces + '- ' + stripped_line[5:].strip()
                org_output.append(org_line)
            else:
                if indent_level > 0:
                    indent_spaces = ' ' * (indent_level * 2)
                    org_line = indent_spaces + stripped_line
                    org_output.append(org_line)
                else:
                    org_output.append(stripped_line)
        else:
            # Remove comments and end document
            if stripped_line.startswith('%') or stripped_line.startswith(r'\end{document}'):
                continue
            org_output.append(stripped_line)

    return org_output





def main():
    # Check if an argument is provided
    if len(sys.argv) < 2:
        print("Usage: python file.py path/to/latex/file.tex")
        sys.exit(1)

    # Extract the LaTeX file path from the arguments
    file_path = sys.argv[1]

    # Determine the directory of the LaTeX file
    latex_file_dir = os.path.dirname(file_path)

    # Determine the output file path
    output_file_name = os.path.splitext(os.path.basename(file_path))[0] + '.org'
    org_output_file_path = os.path.join(latex_file_dir, output_file_name)

    # Read the LaTeX file
    with open(file_path, 'r') as file:
        latex_input = file.readlines()

    # Convert LaTeX to org
    org_output = convert_latex_to_org(latex_input, latex_file_dir)

    # Write the output to the org file
    with open(org_output_file_path, 'w') as file:
        for line in org_output:
            file.write(line + '\n')

    print(f"Converted file saved to: {org_output_file_path}")

if __name__ == "__main__":
    main()



