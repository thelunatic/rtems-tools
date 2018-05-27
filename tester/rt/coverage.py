#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2014 Krzysztof Miesowicz (krzysztof.miesowicz@gmail.com)
# All rights reserved.
#
# This file is part of the RTEMS Tools package in 'rtems-tools'.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from rtemstoolkit import error
from rtemstoolkit import path
from rtemstoolkit import log
from rtemstoolkit import execute
from rtemstoolkit import macros

from datetime import datetime

from . import options

import shutil
import os

try:
    import configparser
except:
    import ConfigParser as configparser

class summary:
    def __init__(self, p_summary_dir):
        self.summary_file_path = path.join(p_summary_dir, 'summary.txt')
        self.index_file_path = path.join(p_summary_dir, 'index.html')
        self.bytes_analyzed = 0
        self.bytes_not_executed = 0
        self.percentage_executed = 0.0
        self.percentage_not_executed = 100.0
        self.ranges_uncovered = 0
        self.branches_uncovered = 0
        self.branches_total = 0
        self.branches_always_taken = 0
        self.branches_never_taken = 0
        self.percentage_branches_covered = 0.0
        self.is_failure = False

    def parse(self):
        if(not path.exists(self.summary_file_path)):
            log.notice('summary file %s does not exist!' % (self.summary_file_path))
            self.is_failure = True
            return

        with open(self.summary_file_path,'r') as summary_file:
           self.bytes_analyzed = self._get_next_with_colon(summary_file)
           self.bytes_not_executed = self._get_next_with_colon(summary_file)
           self.percentage_executed = self._get_next_with_colon(summary_file)
           self.percentage_not_executed = self._get_next_with_colon(summary_file)
           self.ranges_uncovered = self._get_next_with_colon(summary_file)
           self.branches_total = self._get_next_with_colon(summary_file)
           self.branches_uncovered = self._get_next_with_colon(summary_file)
           self.branches_always_taken = self._get_next_without_colon(summary_file)
           self.branches_never_taken = self._get_next_without_colon(summary_file)
        if len(self.branches_uncovered) > 0 and len(self.branches_total) > 0:
            self.percentage_branches_covered = \
            1 - (float(self.branches_uncovered) / float(self.branches_total))
        else:
            self.percentage_branches_covered = 0.0
        return

    def _get_next_with_colon(self, summary_file):
        line = summary_file.readline()
        if ':' in line:
            return line.split(':')[1].strip()
        else:
            return ''

    def _get_next_without_colon(self, summary_file):
        line = summary_file.readline()
        return line.strip().split(' ')[0]

class report_gen_html:
    def __init__(self, p_symbol_sets_list, build_dir, rtdir):
        self.symbol_sets_list = ['score'] 
        self.build_dir = build_dir 
        self.partial_reports_files = list(["index.html", "summary.txt"])
        self.number_of_columns = 1
        self.covoar_src_path = path.join(rtdir, 'covoar')

    def _find_partial_reports(self):
        partial_reports = {}
        for symbol_set in self.symbol_sets_list:
            set_summary = summary(path.join(self.build_dir, "coverage",
                                  symbol_set))
            set_summary.parse()
            partial_reports[symbol_set] = set_summary
        return partial_reports

    def _prepare_head_section(self):
        head_section = '''
        <head>
        <title>RTEMS coverage report</title>
        <style type="text/css">
            progress[value] {
              -webkit-appearance: none;
               appearance: none;

              width: 150px;
              height: 15px;
            }
        </style>
        </head>'''
        return head_section

    def _prepare_index_content(self, partial_reports):
        header = "<h1> RTEMS coverage analysis report </h1>"
        header += "<h3>Coverage reports by symbols sets:</h3>"
        table = "<table>"
        table += self._header_row()
        for symbol_set in partial_reports:
            table += self._row(symbol_set, partial_reports[symbol_set])
        table += "</table> </br>"
        timestamp = "Analysis performed on " + datetime.now().ctime()
        return "<body>\n" + header + table + timestamp + "\n</body>"

    def _row(self, symbol_set, summary):
        row = "<tr>"
        row += "<td>" + symbol_set + "</td>"
        if summary.is_failure:
            row += ' <td colspan="' + str(self.number_of_columns-1) \
            + '" style="background-color:red">FAILURE</td>'
        else:
            row += " <td>" + self._link(summary.index_file_path,"Index") \
            + "</td>"
            row += " <td>" + self._link(summary.summary_file_path,"Summary") \
            + "</td>"
            row += " <td>" + summary.bytes_analyzed + "</td>"
            row += " <td>" + summary.bytes_not_executed + "</td>"
            row += " <td>" + summary.ranges_uncovered + "</td>"
            row += " <td>" + summary.percentage_executed + "%</td>"
            row += " <td>" + summary.percentage_not_executed + "%</td>"
            row += ' <td><progress value="' + summary.percentage_executed \
            + '" max="100"></progress></td>'
            row += " <td>" + summary.branches_uncovered + "</td>"
            row += " <td>" + summary.branches_total + "</td>"
            row += " <td> {:.3%} </td>".format(summary.percentage_branches_covered)
            row += ' <td><progress value="{:.3}" max="100"></progress></td>'.format(100*summary.percentage_branches_covered)
            row += "</tr>\n"
        return row

    def _header_row(self):
        row = "<tr>"
        row += "<th> Symbols set name </th>"
        row += "<th> Index file </th>"
        row += "<th> Summary file </th>"
        row += "<th> Bytes analyzed </th>"
        row += "<th> Bytes not executed </th>"
        row += "<th> Uncovered ranges </th>"
        row += "<th> Percentage covered </th>"
        row += "<th> Percentage uncovered </th>"
        row += "<th> Instruction coverage </th>"
        row += "<th> Branches uncovered </th>"
        row += "<th> Branches total </th>"
        row += "<th> Branches covered percentage </th>"
        row += "<th> Branches coverage </th>"
        row += "</tr>\n"
        self.number_of_columns = row.count('<th>')
        return row

    def _link(self, address, text):
        return '<a href="' + address + '">' + text + '</a>'

    def _create_index_file(self, head_section, content):
        with open(path.join(self.build_dir,"report.html"),'w') as f:
            f.write(head_section)
            f.write(content)

    def generate(self):
        partial_reports = self._find_partial_reports()
        head_section = self._prepare_head_section()
        index_content = self._prepare_index_content(partial_reports)
        self._create_index_file(head_section,index_content)

    def add_covoar_src_path(self):
        table_js_path = path.join(self.covoar_src_path, 'table.js')
        covoar_css_path = path.join(self.covoar_src_path, 'covoar.css')
        for symbol_set in self.symbol_sets_list:
            symbol_set_dir = path.join(self.build_dir, "coverage", symbol_set)
            html_files = os.listdir(symbol_set_dir)
            for html_file in html_files:
                html_file = path.join(symbol_set_dir, html_file)
                if path.exists(html_file) and 'html' in html_file:
                    with open(html_file, 'r') as f:
                        file_data = f.read()
                    file_data = file_data.replace('table.js', table_js_path)
                    file_data = file_data.replace('covoar.css',
                                                  covoar_css_path)
                    with open(html_file, 'w') as f:
                        f.write(file_data)

class build_path_generator(object):
    '''
    Generates the build path from the path to executables
    '''
    def __init__(self, executables):
        self.executables = executables

    def run(self):
        build_path = '/'
        Path = self.executables[0].split('/')
#FIXME : target must be taken from external
        target = 'sparc-rtems5'
        for P in Path:
            if P == target:
                break;
            else:
                build_path = path.join(build_path, P)
        return build_path

class symbol_parser(object):
    '''
    Parse the symbol sets ini and create custom ini file for covoar
    '''
    def __init__(self, symbol_config_path,
                 symbol_select_path, coverage_arg, build_dir):
        self.symbol_select_file = symbol_select_path
        self.symbol_file = symbol_config_path
        self.build_dir = build_dir
        self.symbol_sets = {}
        self.cov_arg = coverage_arg
        self.ssets = []

    def parse(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.symbol_file)
            if self.cov_arg:
                self.ssets = self.cov_arg.split(',')
            else:
                self.ssets = config.get('symbol-sets', 'sets').split(',')
                self.ssets = [ sset.encode('utf-8') for sset in self.ssets]
            for sset in self.ssets:
                lib = path.join(self.build_dir,
                                config.get('libraries', sset))
                self.symbol_sets[sset] = lib.encode('utf-8')
        except:
            raise error.general('Symbol set parsing failed')

    def _write_ini(self):
        config = configparser.ConfigParser()
        try:    
            sets = ', '.join(self.symbol_sets.keys())
            config.add_section('symbol-sets')
            config.set('symbol-sets', 'sets', sets)
            for key in self.symbol_sets.keys():
                config.add_section(key)
                config.set(key, 'libraries', self.symbol_sets[key])
            with open(self.symbol_select_file, 'w') as conf:
                config.write(conf)
        except: 
            raise error.general('write failed')

    def run(self):
        symbol_sets = self.parse()
        self._write_ini()

            
class covoar(object):
    '''
    Covoar runner
    '''
    def __init__(self, base_result_dir, config_dir, executables, explanations_txt):
        self.base_result_dir = base_result_dir
        self.config_dir = config_dir
        self.executables = ' '.join(executables)
        self.explanations_txt = explanations_txt
        self.project_name = 'RTEMS-5'

    def run(self, set_name, symbol_file):
        covoar_result_dir = path.join(self.base_result_dir, set_name)
        if (not path.exists(covoar_result_dir)):
            path.mkdir(covoar_result_dir)
        if (not path.exists(symbol_file)):
            raise error.general('symbol set file: coverage %s was not created for covoar, skipping %s'% (symbol_file, set_name))
        command = ('covoar -S ' + symbol_file
                  + ' -O ' + covoar_result_dir
                  + ' -E ' + self.explanations_txt 
                  + ' -p ' + self.project_name + ' ' + self.executables)
        log.notice('Running covoar for %s' % (set_name))
        print( 'covoar results directory:\n' + covoar_result_dir )
        executor = execute.execute(verbose = True, output = self.output_handler)
        exit_code = executor.shell(command, cwd=os.getcwd())
        if (exit_code[0] != 0):
            raise error.general('covoar failure exit code: %d' % (exit_code[0]))
        log.notice('Coverage run for %s finished successfully.' % (set_name))
        log.notice('-----------------------------------------------')

    def output_handler(self, text):
        log.notice('%s' % (text))

class coverage_run(object):
    '''
    Coverage analysis support for rtems-test
    '''
    def __init__(self, p_macros, coverage_arg):
        '''
        Constructor
        '''
        self.macros = p_macros
        self.build_dir = self.macros['_cwd']
        self.explanations_txt = self.macros.expand(self.macros['cov_explanations'])
        self.test_dir = path.join(self.build_dir, 'coverage')
        if (not path.exists(self.test_dir)):
            path.mkdir(self.test_dir)
        self.rtdir = path.abspath(self.macros['_rtdir'])
        self.rtscripts = self.macros.expand(self.macros['_rtscripts'])
        self.coverage_config_path = path.join(self.rtscripts, 'coverage')
        self.symbol_config_path = path.join(self.coverage_config_path,
                                            'symbol-sets.ini')
        self.symbol_select_path = path.join(self.coverage_config_path,
                                            'symbol-select.ini')
        self.executables = None
        self.symbol_sets = []
        self.no_clean = int(self.macros['_no_clean'])
        self.report_format = self.macros['cov_report_format']
        self.coverage_arg = coverage_arg

    def run(self):
        try:
            if self.executables is None:
                raise error.general('no test executables provided.')
            build_dir = build_path_generator(self.executables).run()
            parser = symbol_parser(self.symbol_config_path,
                                   self.symbol_select_path,
                                   self.coverage_arg,
                                   build_dir)
            parser.run()
            covoar_runner = covoar(self.test_dir, self.symbol_select_path,
                                   self.executables, self.explanations_txt)
            covoar_runner.run('score', self.symbol_select_path)
            self._generate_reports();
            self._summarize();
        finally:
            self._cleanup();

    def _generate_reports(self):
        log.notice('Generating reports')
        if self.report_format == 'html':
            report = report_gen_html(self.symbol_sets,
                                     self.build_dir,
                                     self.rtdir)
            report.generate()
            report.add_covoar_src_path()

    def _cleanup(self):
        if not self.no_clean:
            log.notice('***Cleaning tempfiles***')
            for exe in self.executables:
                trace_file = exe + '.cov'
                if path.exists(trace_file):
                    os.remove(trace_file)

    def _summarize(self):
        log.notice('Coverage analysis finished. You can find results in %s' % (self.build_dir))
