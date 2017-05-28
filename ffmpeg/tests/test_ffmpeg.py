import ffmpeg
import os
import pytest
import subprocess


TEST_DIR = os.path.dirname(__file__)
SAMPLE_DATA_DIR = os.path.join(TEST_DIR, 'sample_data')
TEST_INPUT_FILE = os.path.join(SAMPLE_DATA_DIR, 'dummy.mp4')
TEST_OVERLAY_FILE = os.path.join(SAMPLE_DATA_DIR, 'overlay.png')
TEST_OUTPUT_FILE = os.path.join(SAMPLE_DATA_DIR, 'dummy2.mp4')


subprocess.check_call(['ffmpeg', '-version'])


def test_fluent_equality():
    base1 = ffmpeg.input('dummy1.mp4')
    base2 = ffmpeg.input('dummy1.mp4')
    base3 = ffmpeg.input('dummy2.mp4')
    t1 = base1.trim(start_frame=10, end_frame=20)
    t2 = base1.trim(start_frame=10, end_frame=20)
    t3 = base1.trim(start_frame=10, end_frame=30)
    t4 = base2.trim(start_frame=10, end_frame=20)
    t5 = base3.trim(start_frame=10, end_frame=20)
    assert t1 == t2
    assert t1 != t3
    assert t1 == t4
    assert t1 != t5


def test_fluent_concat():
    base = ffmpeg.input('dummy.mp4')
    trimmed1 = base.trim(start_frame=10, end_frame=20)
    trimmed2 = base.trim(start_frame=30, end_frame=40)
    trimmed3 = base.trim(start_frame=50, end_frame=60)
    concat1 = ffmpeg.concat(trimmed1, trimmed2, trimmed3)
    concat2 = ffmpeg.concat(trimmed1, trimmed2, trimmed3)
    concat3 = ffmpeg.concat(trimmed1, trimmed3, trimmed2)
    concat4 = ffmpeg.concat()
    concat5 = ffmpeg.concat()
    assert concat1 == concat2
    assert concat1 != concat3
    assert concat4 == concat5


def test_fluent_output():
    ffmpeg \
        .input('dummy.mp4') \
        .trim(start_frame=10, end_frame=20) \
        .output('dummy2.mp4')


def test_fluent_complex_filter():
    in_file = ffmpeg.input('dummy.mp4')
    return ffmpeg \
        .concat(
            in_file.trim(start_frame=10, end_frame=20),
            in_file.trim(start_frame=30, end_frame=40),
            in_file.trim(start_frame=50, end_frame=60)
        ) \
        .output('dummy2.mp4')


def test_repr():
    in_file = ffmpeg.input('dummy.mp4')
    trim1 = ffmpeg.trim(in_file, start_frame=10, end_frame=20)
    trim2 = ffmpeg.trim(in_file, start_frame=30, end_frame=40)
    trim3 = ffmpeg.trim(in_file, start_frame=50, end_frame=60)
    concatted = ffmpeg.concat(trim1, trim2, trim3)
    output = ffmpeg.output(concatted, 'dummy2.mp4')
    assert repr(in_file) == "input(filename='dummy.mp4')"
    assert repr(trim1) == "trim(end_frame=20,start_frame=10)"
    assert repr(trim2) == "trim(end_frame=40,start_frame=30)"
    assert repr(trim3) == "trim(end_frame=60,start_frame=50)"
    assert repr(concatted) == "concat(n=3)"
    assert repr(output) == "output(filename='dummy2.mp4')"


def test_get_args_simple():
    out_file = ffmpeg.input('dummy.mp4').output('dummy2.mp4')
    assert out_file.get_args() == ['-i', 'dummy.mp4', 'dummy2.mp4']


def _get_complex_filter_example():
    in_file = ffmpeg.input(TEST_INPUT_FILE)
    overlay_file = ffmpeg.input(TEST_OVERLAY_FILE)
    return ffmpeg \
        .concat(
            in_file.trim(start_frame=10, end_frame=20),
            in_file.trim(start_frame=30, end_frame=40),
        ) \
        .overlay(overlay_file.hflip()) \
        .drawbox(50, 50, 120, 120, color='red', thickness=5) \
        .output(TEST_OUTPUT_FILE) \
        .overwrite_output()


def test_get_args_complex_filter():
    out = _get_complex_filter_example()
    args = ffmpeg.get_args(out)
    assert args == [
        '-i', TEST_INPUT_FILE,
        '-i', TEST_OVERLAY_FILE,
        '-filter_complex',
            '[0]trim=end_frame=20:start_frame=10[v0];' \
            '[0]trim=end_frame=40:start_frame=30[v1];' \
            '[v0][v1]concat=n=2[v2];' \
            '[1]hflip[v3];' \
            '[v2][v3]overlay=eof_action=repeat[v4];' \
            '[v4]drawbox=50:50:120:120:red:t=5[v5]',
        '-map', '[v5]', os.path.join(SAMPLE_DATA_DIR, 'dummy2.mp4'),
        '-y'
    ]


#def test_version():
#    subprocess.check_call(['ffmpeg', '-version'])


def test_run():
    node = _get_complex_filter_example()
    ffmpeg.run(node)


def test_run_dummy_cmd():
    node = _get_complex_filter_example()
    ffmpeg.run(node, cmd='true')


def test_run_dummy_cmd_list():
    node = _get_complex_filter_example()
    ffmpeg.run(node, cmd=['true', 'ignored'])


def test_run_failing_cmd():
    node = _get_complex_filter_example()
    with pytest.raises(subprocess.CalledProcessError):
        ffmpeg.run(node, cmd='false')