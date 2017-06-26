/*
 * SymbolSet.cpp
 *
 *  Created on: Aug 5, 2014
 *      Author: Krzysztof Mięsowicz <krzysztof.miesowicz@gmail.com>
 */

#include "SymbolSet.h"
#include "rld-process.h"
#include "rld.h"
#include <iostream>
#include <fstream>
#include <cstdio>

namespace Symbols {

SymbolSet::SymbolSet() {
	// TODO Auto-generated constructor stub

}

SymbolSet::~SymbolSet() {
	// TODO Auto-generated destructor stub
}

std::string SymbolSet::parseNmOutputLine(std::string line) {
	std::string symbol = "";
	if (line.find("FUNC|") != std::string::npos) {
		symbol = line.substr(0, line.find('|'));
	}
	return symbol;
}

std::string SymbolSet::getLibname(std::string libPath) {
	std::string libname = "", base = "", temp;
	size_t pos = libPath.find_last_of('/');
	if (pos != std::string::npos) {
		temp = libPath.substr(0, pos);
		libname = libPath.substr(pos + 1);
	}
	pos = temp.find_last_of('/');
	if (pos != std::string::npos) {
		base = temp.substr(pos + 1);
	}

	return base + "/" + libname;
}

void SymbolSet::parseNmOutput(std::ifstream& nm_out, const std::string& lib) {
	std::string line, symbol;
	while (getline(nm_out, line)) {
		symbol = parseNmOutputLine(line);
		if (symbol.length() > 0) {
			symbols.push_back(symbol + " " + getLibname(lib));
		}
	}
}

void SymbolSet::generateSymbolFile(std::string filePath, std::string target) {
	std::string nm_output = "nm.out";
	std::string nm_error = "nm.err";
	std::string libFiles;

	for (std::string lib : libraries) {
		try {
			auto status = rld::process::execute(target + "-nm",
					std::vector<std::string> { target + "-nm", "--format=sysv",
							lib }, nm_output, nm_error);
			if (status.type != rld::process::status::normal
					or
					status.code != 0) {
				std::cout << "ERROR: nm returned " << status.code << std::endl;
				std::cout << "For details see " << nm_error << " file." << std::endl;
				std::remove(nm_output.c_str());
				return;
			}

		} catch (rld::error& err) {
			std::cout << "Error while running nm for " + lib << std::endl;
			std::cout << err.what << " in " << err.where << std::endl;
			return;
		}

		std::ifstream nm_out(nm_output);
		try {
			parseNmOutput(nm_out, lib);
		} catch(std::exception& e) {
			std::cout << "ERROR while parsing nm output: " << e.what() << std::endl;
		}
		nm_out.close();
	}

	std::remove(nm_output.c_str());
	std::remove(nm_error.c_str());

	std::ofstream outputFile(filePath);
	for (std::string symbol : symbols) {
		outputFile << symbol << std::endl;
	}
	outputFile.close();
}

} /* namespace Symbols */
