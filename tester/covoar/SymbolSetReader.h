/*
 * SymbolSetReader.h
 *
 *  Created on: Aug 5, 2014
 *      Author: Krzysztof Mięsowicz <krzysztof.miesowicz@gmail.com>
 */

#ifndef SYMBOLSETREADER_H_
#define SYMBOLSETREADER_H_

#include <string>
#include <vector>
#include <utility>
#include "SymbolSet.h"

using namespace std;

namespace Symbols {

class SymbolSetReader {
public:
	SymbolSetReader();
	virtual ~SymbolSetReader();

	vector<SymbolSet> readSetFile(string filepath);
protected:
	pair<string, string> parseLine(string line);
private:
	string& trim(string& str);
};

} /* namespace Symbols */

#endif /* SYMBOLSETREADER_H_ */
