import argparse
import re
from pathlib import Path


class Stack:
    def __init__(self):
        self._li = []
        self.push_pop_op_cnt = 0

    def size(self):
        return len(self._li)

    def clear(self):
        self._li.clear()

    def push(self, value):
        assert value is not None
        self.push_pop_op_cnt += 1
        self._li.append(value)

    def pop(self, expected_value=None, default=None):
        self.push_pop_op_cnt -= 1
        if expected_value is not None:
            if not (self._li and (self._li[-1] == expected_value)):
                print('WARN: pop not expected value!')
        if default is None:
            return self._li.pop()
        else:
            return self._li.pop() if self._li else default

    def top(self, default=None):
        if default is None:
            return self._li[-1]
        else:
            return self._li[-1] if self._li else default

    def toptop(self, default=None):
        if default is None:
            return self._li[-2]
        else:
            return self._li[-2] if len(self._li) >= 2 else default

    def at_top(self, value) -> bool:
        return (self._li[-1] == value) if self._li else False


class SnoopLineParser:
    """parse snoop line"""

    def __init__(self, indent_char: str = ' '):
        self._indent_char = indent_char
        assert self._indent_char

    # def indent_level(self, line):
    #     pattern = r'^(' + self._indent_char + r'+)[^' + self._indent_char + r'].*$'
    #     m = re.match(pattern, line)
    #     if not m:
    #         return
    #     indentchars = m.group(1)
    #     assert indentchars and len(indentchars) % 4 == 0
    #
    #     indent_level = len(indentchars) // 4
    #     return indent_level

    def source_path_info(self, line):
        pattern = r'^(' + self._indent_char + r'{4,})Source path:\.\.\.\s*(\S.*)$'
        m = re.match(pattern, line)
        if not m:
            return
        indentchars = m.group(1)
        filepath = m.group(2)
        assert len(indentchars) % 4 == 0

        indent_level = len(indentchars) // 4
        return indent_level, filepath

    def func_line_event(self, line):
        pattern = r'^(' + self._indent_char + r'{4,})(\d{2}:\d{2}:\d{2}.\d{6})\s*\[line\s*(\d+)\]\s*(\S.*)$'
        m = re.match(pattern, line)
        if not m:
            return
        indentchars = m.group(1)
        timestamp = m.group(2)
        linenum = int(m.group(3))
        funccode = m.group(4)
        assert len(indentchars) % 4 == 0

        indent_level = len(indentchars) // 4
        return indent_level, linenum, funccode

    def func_call_event(self, line):
        pattern = r'^(' + self._indent_char + r'{4,})(\d{2}:\d{2}:\d{2}.\d{6})\s*\[call\s*(\d+)\]\s*(\S.*)$'
        m = re.match(pattern, line)
        if not m:
            return
        indentchars = m.group(1)
        timestamp = m.group(2)
        linenum = int(m.group(3))
        funccode = m.group(4)
        assert len(indentchars) % 4 == 0

        indent_level = len(indentchars) // 4
        return indent_level, linenum, funccode

    def func_call_arguments_info(self, line):
        pattern = r'^(' + self._indent_char + r'{4,})Pass arguments:\s*{.+$'
        m = re.match(pattern, line)
        if not m:
            return
        indentchars = m.group(1)
        assert len(indentchars) % 4 == 0

        indent_level = len(indentchars) // 4
        return indent_level

    def func_return_event(self, line):
        pattern = r'^(' + self._indent_char + r'{4,})(\d{2}:\d{2}:\d{2}.\d{6})\s*\[return\s*(\d+)\]\s*(\S.*)$'
        m = re.match(pattern, line)
        if not m:
            return
        indentchars = m.group(1)
        timestamp = m.group(2)
        linenum = int(m.group(3))
        retvalue = m.group(4)
        assert len(indentchars) % 4 == 0

        indent_level = len(indentchars) // 4
        return indent_level, linenum, retvalue

    def func_return_value_info(self, line):
        pattern = r'^(' + self._indent_char + r'{4,})Return value:\.\.\s*<?.+$'
        m = re.match(pattern, line)
        if not m:
            return
        indentchars = m.group(1)
        assert len(indentchars) % 4 == 0

        indent_level = len(indentchars) // 4
        return indent_level


def xform(s: str):
    """
    replace < or > to ^, to make mermaidjs work.

    Bug: https://github.com/mermaid-js/mermaid/issues/4390
    """
    return re.sub(r'<|>', '^', s)


def main_impl(inputfile, outputfile, args):
    html_above = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Diagram</title>
        <style>
            :hover {stroke: lime!important;}
            :active {stroke: red!important;}
        </style>
    </head>
    <body>
      <div id="main">
        <!-- mermaid diagram: -->
        <pre class="mermaid">
"""

    html_below = """
        </pre>

        <script type="module">
            // import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
            import mermaid from "https://unpkg.com/mermaid@10/dist/mermaid.esm.min.mjs";
            mermaid.initialize({ startOnLoad:true, securityLevel:'loose', maxTextSize:999999999 });
        </script>
        <script src='https://unpkg.com/panzoom@9.4/dist/panzoom.min.js'></script>
        <script>
            const main_container = document.querySelector('#main');
            panzoom(main_container, {smoothScroll: false});
        </script>
      </div>
    </body>
</html>
"""

    with open(inputfile, encoding='utf-8') as fd:
        logfile_lines = tuple(map(lambda x: x.rstrip(), fd.readlines()))

    with open(outputfile, mode='w', encoding='utf-8') as fd:
        print(html_above, file=fd)
        print(r'%%{init: {"flowchart": {"useMaxWidth":0, "curve":"natural"}} }%%', file=fd)
        print('flowchart LR', file=fd)

        stack = Stack()
        parser = SnoopLineParser(args.indent_char)
        nth = 0
        log_line_index = -1
        while True:
            log_line_index += 1
            if log_line_index >= len(logfile_lines):
                break
            line = logfile_lines[log_line_index]

            # file
            mf = parser.source_path_info(line)
            # call
            mc = parser.func_call_event(line)
            # return
            # mr = parser.func_return_event(line)

            if not (mf or mc):
                continue

            caller_file = None
            callee_file = None

            if mf:
                indent_level, sourcepath = mf
                if log_line_index == 0:
                    stack.push(sourcepath)
                    continue

                prev2_line = logfile_lines[log_line_index - 2]
                prev_line = logfile_lines[log_line_index - 1]
                next_line = logfile_lines[log_line_index + 1]

                flag_run_below = True
                for _ in range(1):
                    # call in
                    pre = parser.func_line_event(prev_line)
                    nxt = parser.func_call_event(next_line)
                    if pre is not None and nxt is not None:
                        pre_indent_level, *_ = pre
                        nxt_indent_level, *_ = nxt
                        assert pre_indent_level < indent_level == nxt_indent_level
                        stack.push(sourcepath)
                        caller_file = stack.toptop()
                        callee_file = stack.top()

                        log_line_index += 1
                        mc = nxt
                        break

                    # function return
                    pre2 = parser.func_return_event(prev2_line)
                    pre = parser.func_return_value_info(prev_line)
                    nxt = parser.func_line_event(next_line)
                    nxt_ = parser.func_return_event(next_line)
                    if pre2 is not None and pre is not None and (nxt is not None or nxt_ is not None):
                        pre2_indent_level, *_ = pre2
                        pre_indent_level = pre
                        nxt_indent_level, *_ = nxt or nxt_
                        assert pre2_indent_level == pre_indent_level > indent_level == nxt_indent_level
                        stack.pop()
                        assert sourcepath == stack.top()
                        flag_run_below = False
                        break

                    # attribute return: e.g.:args.modelname
                    pre2 = parser.func_return_event(prev2_line)
                    pre = parser.func_return_value_info(prev_line)
                    nxt = parser.func_call_event(next_line)
                    if pre2 is not None and pre is not None and nxt is not None:
                        pre2_indent_level, *_ = pre2
                        pre_indent_level = pre
                        nxt_indent_level, *_ = nxt
                        assert pre2_indent_level == pre_indent_level == indent_level == nxt_indent_level  # yes,pre==current
                        stack.pop()  # pop the same level file
                        stack.push(sourcepath)

                        caller_file = stack.toptop()
                        callee_file = stack.top()
                        mc = nxt
                        log_line_index += 1
                        break

                    # no other cases
                    pass
                if not flag_run_below:
                    continue
                assert caller_file and callee_file

            nth += 1
            indent_level, linenum, funccode = mc
            if not (caller_file and callee_file):
                caller_file = callee_file = stack.top()

            style = ' style="color:olive"' if caller_file == callee_file else ''
            tooltip = f'CALLSTACK={indent_level}: {caller_file} CALL {callee_file} LINE={linenum}, CODE={funccode}'
            callee_name = Path(callee_file).name
            if True:
                tooltip = xform(tooltip)
                caller_file = xform(caller_file)
                callee_file = xform(callee_file)
                callee_name = xform(callee_name)
                funccode = xform(funccode)
            statement = f'{caller_file} --> |<span title="{tooltip}"{style}> #<b>{nth}</b> &{log_line_index + 1}: {callee_name} {linenum}, {funccode}</span>| {callee_file}'
            print(f'  {statement}', file=fd)

        stack.pop()  # the first-pushed one
        print(html_below, file=fd)
        if stack.push_pop_op_cnt != 0:
            print(f'WARN: unbalanced call-return pair, {stack.push_pop_op_cnt}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', required=True, help='input log file')
    parser.add_argument('-o', '--outputfile', help='output html file')
    parser.add_argument('-c', '--indent-char', default='-', help='indent char')
    # parser.add_argument('-r', '--include-return', action='store_true', help='include return statements')
    args = parser.parse_args()
    print(args)
    assert args.indent_char, 'indent char not specified!'
    inputfile = args.inputfile
    outputfile = args.outputfile
    if not outputfile:
        outputfile = inputfile[:-len(Path(inputfile).suffix)] + '.html'

    main_impl(inputfile, outputfile, args)
    print('Saved to:', outputfile)


if __name__ == "__main__":
    main()
