/*
 * SymbolSetReader.cpp
 *
 *  Created on: Aug 5, 2014
 *      Author: Krzysztof Mięsowicz <krzysztof.miesowicz@gmail.com>
 */

#include "SymbolSetReader.h"
#include "iostream"
#include "fstream"

namespace Symbols {

SymbolSetReader::SymbolSetReader() {
	// TODO Auto-generated constructor stub

}

SymbolSetReader::~SymbolSetReader() {
	// TODO Auto-generated destructor stub
}

std::vector<SymbolSet> SymbolSetReader::readSetFile(string filepath) {
	std::vector<SymbolSet> setList { };
	ifstream file(filepath);
	string line;
	while (getline(file, line)) {
		if (line.find("symbolset:") != std::string::npos) {
			setList.emplace_back();
		} else if (line.length() > 0) {

			auto pair = parseLine(line);

			if(pair.first == "name") {
				if (setList.empty()) {
					setList.emplace_back();
				}
				setList.rbegin()->setName(pair.second);
				continue;
			}
			if(pair.first == "lib") {
				setList.rbegin()->addLibrary(pair.second);
				continue;
			}

			std::cout << "Invalid entry in configuration file : " << line << endl;
			break;
		}
	}
	file.close();
	return setList;
}

std::pair<string, string> SymbolSetReader::parseLine(string line) {
	size_t delimeterPosition = line.find('=');

	if (delimeterPosition != std::string::npos) {
		string key = line.substr(0, delimeterPosition);
		string value = line.substr(delimeterPosition + 1);
		return {trim(key), trim(value)};
	}

	return {"",""};
}

string& SymbolSetReader::trim(string& str) {
	// trim trailing spaces
	size_t endpos = str.find_last_not_of(" \t\n\r");
	if (string::npos != endpos) {
		str = str.substr(0, endpos + 1);
	}

	// trim leading spaces
	size_t startpos = str.find_first_not_of(" \t\n\r");
	if (string::npos != startpos) {
		str = str.substr(startpos);
	}

	return str;
}

} /* namespace Symbols */
