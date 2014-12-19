import pytest

from .capture_subprocess import capture_subprocess
from testing import coverage_warnings_regex


def make_outputter():
    """Create the the outputter.py script, for the demonstration."""
    with open('outputter.py', 'w') as outputter:
        outputter.write('''\
from __future__ import print_function
from __future__ import division
from sys import stdout, stderr
from time import sleep
from random import random, seed
seed(0)  # unpredictable, but repeatable

# system should not deadlock for any given value of these parameters.
LINES = 4000
TIME = 0
WIDTH = 179
ERROR_RATIO = .20

for i in range(LINES):
    if random() > ERROR_RATIO:
        char = '.'
        file = stdout
    else:
        char = '%'
        file = stderr

    for j in range(WIDTH):
        print(char, file=file, end='')
        file.flush()
        sleep(TIME / LINES / WIDTH)
    print(file=file)
    file.flush()
''')


# buglet: floating-point, zero, negative values interpreted as infinite =/
@pytest.mark.flaky(reruns=5)
@pytest.mark.timeout(12)  # ~50% at 6 seconds
def test_capture_subprocess(tmpdir):
    tmpdir.chdir()
    make_outputter()

    cmd = ('python', 'outputter.py')
    stdout, stderr, combined = capture_subprocess(cmd)

    stderr = coverage_warnings_regex.sub('', stderr)
    combined = coverage_warnings_regex.sub('', combined)

    assert stdout.count('\n') == 3207
    assert stderr.count('\n') == 793
    assert combined.count('\n') == 4000

    assert stdout.strip('.\n') == ''
    assert stderr.strip('%\n') == ''

    # I'd like to also assert that the two streams are interleaved strictly by line,
    # but I haven't been able to produce such output reliably =/

    # instead, we assert that all individual characters are preserved in the combination
    histogram = {}
    for string in (stderr, stdout):
        for char in string:
            histogram[char] = histogram.get(char, 0) + 1
    for char in histogram:
        combined = combined.replace(char, '', histogram[char])
    assert combined == '', histogram