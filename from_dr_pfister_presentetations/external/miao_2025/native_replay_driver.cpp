// Audit driver for the Miao et al. C++ reference implementation.
// Compile against their pinned repository after applying native_replay.patch.
// Input: one whitespace-separated I=0,X=1,Z=2,Y=3 Pauli vector per line.
// Output: one JSON record per input shot. The source decoder math is unchanged.

#include "stabilizerCodes.h"

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

int main() {
    fileReader matrices(32, 2, 30, stabilizerCodesType::toric, false);
    std::string line;
    unsigned shot = 0;
    while (std::getline(std::cin, line)) {
        std::istringstream stream(line);
        std::vector<unsigned> error;
        unsigned value;
        while (stream >> value) error.push_back(value);
        if (error.size() != 32) throw std::runtime_error("expected 32 Pauli values per shot");
        stabilizerCodes code(32, 2, 30, stabilizerCodesType::toric, matrices, false);
        code.set_error_for_replay(error);
        auto result = code.decode(25, 0.1);
        std::cout << "{\"shot\":" << shot
                  << ",\"valid_syndrome\":" << (result[0] ? "true" : "false")
                  << ",\"success\":" << (result[1] ? "true" : "false") << "}\n";
        ++shot;
    }
    return 0;
}
