/*
 * SymbolSet.h
 *
 *  Created on: Aug 5, 2014
 *      Author: Krzysztof Mięsowicz <krzysztof.miesowicz@gmail.com>
 */

#ifndef SYMBOLSET_H_
#define SYMBOLSET_H_

#include <string>
#include <vector>

#include "rld-process.h"

namespace Symbols {

class SymbolSet {
public:
	SymbolSet();
	virtual ~SymbolSet();

	const std::string getName() const {
		return name;
	}

	void setName(const std::string& name) {
		this->name = name;
	}

	const std::vector<std::string> getLibraries() const {
		return libraries;
	}

	void addLibrary(std::string libraryPath) {
		libraries.push_back(libraryPath);
	}

	void generateSymbolFile(rld::process::tempfile& filePath,
                            std::string target);

private:
	std::string name;
	std::vector<std::string> libraries;
	std::vector<std::string> symbols;

	std::string parseNmOutputLine(std::string line);
	std::string getLibname(std::string libPath);
	void parseNmOutput(std::ifstream& nm_out, const std::string& lib);
};

} /* namespace Symbols */

#endif /* SYMBOLSET_H_ */
