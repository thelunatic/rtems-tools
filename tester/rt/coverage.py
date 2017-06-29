'''
Created on Jul 7, 2014

@author: Krzysztof Miesowicz <krzysztof.miesowicz@gmail.com>
'''
from rtemstoolkit import path
from rtemstoolkit import log
from rtemstoolkit import execute
from rtemstoolkit import macros
import shutil
import os
from datetime import datetime

class summary:
    def __init__(self, p_summaryDir):
        self.summaryFilePath = path.join(p_summaryDir, "summary.txt")
        self.indexFilePath = path.join(p_summaryDir, "index.html")
        self.bytes_analyzed = 0
        self.bytes_notExecuted = 0
        self.percentage_executed = 0.0
        self.percentage_notExecuted = 100.0
        self.ranges_uncovered = 0
        self.branches_uncovered = 0
        self.branches_total = 0
        self.branches_alwaysTaken = 0
        self.branches_neverTaken = 0
        self.percentage_branchesCovered = 0.0
        self.isFailure = False

    def parse(self):
        if(not path.exists(self.summaryFilePath)):
            log.warning("Summary file " + self.summaryFilePath + " does not exist!")
            self.isFailure = True
            return

        summaryFile = open(self.summaryFilePath,'r')
        self.bytes_analyzed = self._getValueFromNextLineWithColon(summaryFile)
        self.bytes_notExecuted = self._getValueFromNextLineWithColon(summaryFile)
        self.percentage_executed = self._getValueFromNextLineWithColon(summaryFile)
        self.percentage_notExecuted = self._getValueFromNextLineWithColon(summaryFile)
        self.ranges_uncovered = self._getValueFromNextLineWithColon(summaryFile)
        self.branches_total = self._getValueFromNextLineWithColon(summaryFile)
        self.branches_uncovered = self._getValueFromNextLineWithColon(summaryFile)
        self.branches_alwaysTaken = self._getValueFromNextLineWithoutColon(summaryFile)
        self.branches_neverTaken = self._getValueFromNextLineWithoutColon(summaryFile)
        summaryFile.close()

        self.percentage_branchesCovered = 1 - float(self.branches_uncovered) / float(self.branches_total)
        return

    def _getValueFromNextLineWithColon(self, summaryFile):
        line = summaryFile.readline()
        return line.split(':')[1].strip()

    def _getValueFromNextLineWithoutColon(self, summaryFile):
        line = summaryFile.readline()
        return line.strip().split(' ')[0]

class reportGen:
    def __init__(self, p_symbolSetsList, p_targetDir):
        self.symbolSetsList = p_symbolSetsList
        self.targetDir = p_targetDir
        self.partialReportsFiles = list(["index.html", "summary.txt"])
        self.numberOfColumns = 1

    def _findPartialReports(self):
        partialReports = {}
        for symbolSet in self.symbolSetsList:
            setSummary = summary(path.join(self.targetDir, "test", symbolSet))
            setSummary.parse()
            partialReports[symbolSet] = setSummary
        return partialReports

    def _prepareHeadSection(self):
        headSection = '''
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
        return headSection

    def _prepareIndexContent(self, partialReports):
        header = "<h1> RTEMS coverage analysis report </h1>"
        header += "<h3>Coverage reports by symbols sets:</h3>"
        table = "<table>"
        table += self._headerRow()
        for symbolSet in partialReports:
            table += self._row(symbolSet, partialReports[symbolSet])
        table += "</table> </br>"
        timestamp = "Analysis performed on " + datetime.now().ctime()
        return "<body>\n" + header + table + timestamp + "\n</body>"

    def _row(self, symbolSet, summary):
        row = "<tr>"
        row += "<td>" + symbolSet + "</td>"
        if summary.isFailure:
            row += ' <td colspan="' + str(self.numberOfColumns-1) + '" style="background-color:red">FAILURE</td>'
        else:
            row += " <td>" + self._link(summary.indexFilePath,"Index") + "</td>"
            row += " <td>" + self._link(summary.summaryFilePath,"Summary") + "</td>"
            row += " <td>" + summary.bytes_analyzed + "</td>"
            row += " <td>" + summary.bytes_notExecuted + "</td>"
            row += " <td>" + summary.ranges_uncovered + "</td>"
            row += " <td>" + summary.percentage_executed + "%</td>"
            row += " <td>" + summary.percentage_notExecuted + "%</td>"
            row += ' <td><progress value="' + summary.percentage_executed + '" max="100"></progress></td>'
            row += " <td>" + summary.branches_uncovered + "</td>"
            row += " <td>" + summary.branches_total + "</td>"
            row += " <td> {:.3%} </td>".format(summary.percentage_branchesCovered)
            row += ' <td><progress value="{:.3}" max="100"></progress></td>'.format(100*summary.percentage_branchesCovered)
            row += "</tr>\n"
        return row

    def _headerRow(self):
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
        self.numberOfColumns = row.count('<th>')
        return row

    def _link(self, address, text):
        return '<a href="' + address + '">' + text + '</a>'

    def _createIndexFile(self, headSection, content):
        f = open(path.join(self.targetDir, "report.html"),"w")
        try:
            f.write(headSection)
            f.write(content)
        finally:
            f.close()

    def generate(self):
        partialReports = self._findPartialReports()
        headSection = self._prepareHeadSection()
        indexContent = self._prepareIndexContent(partialReports)
        self._createIndexFile(headSection,indexContent)
#         _createSummaryFile(summaryContent)

class symbolsConfiguration(object):
    '''
    Manages symbols configuration - reading from symbol file
    '''
    def __init__(self):
        self.symbolSets = []

    def _log_invalid_format(self):
        log.stderr("Invalid symbol configuration file")
        log.stderr(''' Configuration file format:
                symbolset:
                   name=SYMBOLSET_NAME
                   lib=PATH_TO_LIBRARY_1
                   lib=PATH_TO_LIBRARY_2
                symbolset:
                    name=SYMBOLSET_NAME_N
                    lib=PATH_TO_LIBRARY        ''')

    def load(self, symbolSetConfigFile):
        scf = open(symbolSetConfigFile, 'r')
        for line in scf:
            try:
                if line.strip().startswith("symbolset"):
                    self.symbolSets.append(symbolSet("",[]))
                else:
                    splitted = line.split('=')
                    if(len(splitted) == 2):
                        key = splitted[0].strip()
                        value = splitted[1].strip()
                        if key == 'name':
                            self.symbolSets[-1].name = value
                        elif key == 'lib':
                            self.symbolSets[-1].libs.append(value)
                        else:
                            log.stderr("Invalid key : " + key + " in symbol set configuration file " + symbolSetConfigFile)
                    else:
                        self._log_invalid_format()
            except:
                self._log_invalid_format()
        scf.close()

    def save(self, path):
        scf = open(path, 'w')
        for sset in self.symbolSets:
            sset.writeSetFile(path)
        scf.close()

class symbolSet(object):
    def __init__(self, name, libs):
        self.name = name
        self.libs = libs

    def isValid(self):
        if len(self.name) == 0:
            log.stderr("Invalid symbol set. Symbol set must have name! ")
            return False
        if len(self.libs) == 0:
            log.stderr("Invalid symbol set. Symbol set must have specified libraries!")
            return False
        for lib in self.libs:
            if not path.exists(lib):
                log.stderr("Invalid library path: " + lib)
                return False
        return True

    def writeSetFile(self, path):
        f = open(path, 'w')
        f.write("symbolset:\n")
        f.write("\t name=" + self.name + '\n')
        for lib in self.libs:
            f.write("\t lib=" + lib + '\n')
        f.close()

class covoar(object):
    '''
    Covoar runner
    '''

    def __init__(self, baseResultDir, configDir, tracesDir, covoarSrcDir):
        self.baseResultDir = baseResultDir
        self.configDir = configDir
        self.tracesDir = tracesDir
        self.covoarSrcDir = covoarSrcDir

    def run(self, setName, covoarConfigFile, symbolFile):
        covoarResultDir = path.join(self.baseResultDir, setName)

        if (not path.exists(covoarResultDir)):
            path.mkdir(covoarResultDir)

        if (not path.exists(symbolFile)):
            log.stderr("Symbol set file: " + symbolFile + " doesn't exists! Covoar can not be run!")
            log.stderr("Skipping " + setName)
            return

        command = "covoar -C" + covoarConfigFile + " -S " + symbolFile + " -O " + covoarResultDir + " " + path.join(self.tracesDir, "*.exe")
        log.notice("Running covoar for " + setName, stdout_only=True)
        log.notice(command, stdout_only=True)
        executor = execute.execute(verbose=True, output=output_handler)
        exit_code = executor.shell(command, cwd=os.getcwd())
        shutil.copy2(path.join(self.covoarSrcDir, 'table.js'), path.join(covoarResultDir, 'table.js'))
        shutil.copy2(path.join(self.covoarSrcDir, 'covoar.css'), path.join(covoarResultDir, 'covoar.css'))
        log.notice("Coverage run for " + setName + " finished ")
        status = "success"
        if (exit_code[0] != 0):
            status = "failure. Error code: " + str(exit_code[0])
        log.notice("Coverage run for " + setName + " finished " + status)
        log.notice("-----------------------------------------------")

class coverage_run(object):
    '''
    Coverage analysis support for rtems-test
    '''

    def __init__(self, p_macros):
        '''
        Constructor
        '''
        self.macros = p_macros
        self.targetDir = self.macros['_cwd']
        self.testDir = path.join(self.targetDir, "test")
        self.rtdir = path.abspath(self.macros['_rtdir'])
        self.rtscripts = self.macros.expand(self.macros['_rtscripts'])
        self.coverageConfigPath = path.join(self.rtscripts, "coverage")
        self.symbolConfigPath = path.join(self.coverageConfigPath, "symbolSets.config")
        self.tracesDir = path.join(self.targetDir, 'coverage')
        self.config_map = self.macros.macros['coverage']
        self.executables = None
        self.symbolSets = []

    def prepareEnvironment(self):
        if(path.exists(self.tracesDir)):
            path.removeall(self.tracesDir)
        path.mkdir(self.tracesDir)
        log.notice("Coverage environment prepared", stdout_only = True)

    def writeCovoarConfig(self, covoarConfigFile):
        ccf = open(covoarConfigFile, 'w')
        ccf.write("format = " + self.config_map['format'][2] + '\n')
        ccf.write("target = " + self.config_map['target'][2] + '\n')
        ccf.write("explanations = " + self.macros.expand(self.config_map['explanations'][2]) + '\n')
        ccf.write("coverageExtension = " + self.config_map['coverageextension'][2] + '\n')
        ccf.write("gcnosFile = " + self.macros.expand(self.config_map['gcnosfile'][2]) + '\n')
        ccf.write("executableExtension = " + self.config_map['executableextension'][2] + '\n')
        ccf.write("projectName = " + self.config_map['projectname'][2] + '\n')
        ccf.close()

    def run(self):
        if self.executables == None:
            log.stderr("ERROR: Executables for coverage analysis unspecified!")
            raise Exception('Executable for coverage analysis unspecified')
        if self.config_map == None:
            log.stderr("ERROR: Configuration map for coverage analysis unspecified!")
            raise Exception("ERROR: Configuration map for coverage analysis unspecified!")

        covoarConfigFile = path.join(self.tracesDir, 'config')
        self.writeCovoarConfig(covoarConfigFile)
        if(not path.exists(covoarConfigFile)):
            log.stderr("Covoar configuration file: " + path.abspath(covoarConfigFile) + " doesn't exists! Covoar can not be run! ");
            return -1

        self._linkExecutables()

        symbolConfig = symbolsConfiguration()
        symbolConfig.load(self.symbolConfigPath)

        for sset in symbolConfig.symbolSets:
            if sset.isValid():
                symbolSetFile = path.join(self.tracesDir, sset.name + ".symcfg")
                sset.writeSetFile(symbolSetFile)
                self.symbolSets.append(sset.name)

                covoar_run = covoar(self.testDir, self.symbolConfigPath, self.tracesDir, path.join(self.rtdir, 'covoar'))
                covoar_run.run(sset.name, covoarConfigFile, symbolSetFile)
            else:
                log.stderr("Invalid symbol set " + sset.name + ". Skipping covoar run.")

        self._generateReports();
        self._cleanup();
        self._summarize();

    def _linkExecutables(self):
        log.notice("Linking executables to " + self.tracesDir)

        for exe in self.executables:
            dst = path.join(self.tracesDir, path.basename(exe))
            os.link(exe, dst)
        log.notice("Symlinks made")

    def _generateReports(self):
        log.notice("Generating reports")
        report = reportGen(self.symbolSets, self.targetDir)
        report.generate()

    def _cleanup(self):
        log.notice("Cleaning workspace up")
        path.removeall(self.tracesDir)

    def _summarize(self):
        log.notice("Coverage analysis finished. You can find results in " + self.targetDir)

def output_handler(text):
    log.notice(text, stdout_only = False)

if __name__ == "__main__":
    c = coverage_run("/home/cpod/coverage_test","/home/cpod/development/rtems/test/rtems-tools/tester")
    c.prepareEnvironment()
    c.executables = ["/home/cpod/development/rtems/leon3/sparc-rtems4.12/c/leon3/testsuites/samples/hello/hello.ralf"]
    c.run()
