"""Effective configuration and retained-file checks for bounded diagnostics."""
import configparser
import re
from pathlib import Path


def normalized_configuration(path, bench, output):
    parser=configparser.ConfigParser(interpolation=None)
    parser.optionxform=str
    parser.read_string(Path(path).read_text())
    result={}
    output_prefix=str(Path(output)).replace(str(Path(__file__).resolve().parents[1]),'/project')
    for section in parser.sections():
        for key,value in parser[section].items():
            value=value.replace(output_prefix,'@OUTPUT@')
            value=value.replace(bench,'@KERNEL@')
            value=re.sub(r'/project/\.artifacts/[^/]+/integration-test/with-cpu/[^/\s]+','@WORK@',value)
            # config.ini redirects use only the current run's output root.
            value=re.sub(r'/project/results/diagnostics/[^/]+/(?:base|tiled2|tiled4)/(?:full|invocation)/(?:reference|instrumented)', '@OUTPUT@',value)
            value=re.sub(r'/project/results/diagnostics/[^/]+/(?:matched|unchanged)_(?:base|tiled2|tiled4)/(?:correctness|timed)', '@OUTPUT@',value)
            value=value.replace('gemm_cache_pilot.cfg','@KERNEL_CONFIG@').replace('@KERNEL@.cfg','@KERNEL_CONFIG@')
            if key=='outputPrefix': value='@MODEL_OUTPUT@'
            result[section.replace(bench,'@KERNEL@'),key]=value
    return result
